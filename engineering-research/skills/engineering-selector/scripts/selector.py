"""Engineering Selector V1 deterministic layer: the orchestration state machine.

  python skills/engineering-selector/scripts/selector.py init   --state STATE.json --statement STATEMENT.txt
  python skills/engineering-selector/scripts/selector.py record --state STATE.json --artifact ARTIFACT.json
  python skills/engineering-selector/scripts/selector.py answer --state STATE.json --answer ANSWER.json
  python skills/engineering-selector/scripts/selector.py status --state STATE.json [--json]
  python skills/engineering-selector/scripts/selector.py result --state STATE.json
  python skills/engineering-selector/scripts/selector.py request --state STATE.json   (RUN request text)

The model does the engineering work with the existing skills (problem-router, field-design-expert,
capability-resolver, engineering-research, engineering-research-critic). This script keeps the
SELECTION_STATE and decides, mechanically, which stage comes next and whether an artifact or a human
answer is allowed at the current stage. It refuses (exit 1, state unchanged) anything out of order:
- a design-led or hybrid problem never reaches product research before its design gate is approved;
- a selection-led problem is not redesigned (no Field/Design Expert stage);
- the Capability Resolver runs only for a genuine capability gap (a need the registry does not cover);
- external discovery needs a human approval and the review gate; nothing is installed or connected;
- product research (candidates, CHECK_RESULT) happens only inside the RUN stage after G1 approval;
- at G1 every draft-SPEC row is classified USER_STATED, USER_APPROVED, PROPOSED_ENGINEERING_CONSTRAINT
  or UNKNOWN (g1_semantics.py, O-P6-01); a proposed constraint never becomes an approved HARD
  requirement without the human's explicit APPROVE, and after G1 no HARD row may differ from the
  approved one;
- every RUN leader goes to an independent critic, and a critic that changed the result (labels 1-3),
  or an invalid critic result, can never become a final answer without the RUN applying it;
- G2 is a decision point, not the end: ADDITIONAL_RESEARCH and VERIFY_DIFFERENT_CANDIDATE return to the
  RUN (SPEC, G1 approval and evidence kept; the next RUN stop must carry a newer CHECK_RESULT);
  REOPEN_SPEC returns to G1 (a new explicit APPROVE_SPEC is needed before research); ADVANCE_TO_VERIFICATION
  needs a preferred candidate and finalizes only on a critic PASS (label 4 on that leader, applied by the
  RUN), otherwise it sends the leader to a fresh-session critic first; ACCEPT_NONE or STOP ends the
  selection with no recommendation. The result is terminal only after a critic PASS or that explicit
  human stop, and every G2 transition and every superseded round is kept in the state history;
- every critic finding is classified MATERIAL, NON_MATERIAL or INSUFFICIENT_EVIDENCE (materiality.py,
  O-P6-03) and kept in critic_findings with every re-assessment; only a missed qualifying candidate that
  passes every HARD requirement on manufacturer evidence and is dominated by the leader on the G1-approved
  ranking is NON_MATERIAL. A leader is final only when its own fresh critic pass is clean (label 4, or
  label 3 with every finding NON_MATERIAL) and no MATERIAL or INSUFFICIENT_EVIDENCE finding remains open;
- a value the user put out of scope never becomes a requirement or an in-scope search item.
Judgment (routing signals, design content, evidence, critic findings) stays with the model and the
human, exactly as in the skills it calls. Standard-library Python 3.10+, no network.
Exit 0 OK, 1 refused / not allowed, 2 bad input.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parents[1]
REPO = HERE.parents[2]
for extra in (HERE, SKILLS / "problem-router" / "scripts", SKILLS / "field-design-expert" / "scripts",
              SKILLS / "capability-resolver" / "scripts", REPO / "er-core"):
    if extra.is_dir():
        sys.path.insert(0, str(extra))

import fde_check  # noqa: E402
import g1_semantics as G1  # noqa: E402
import materiality as M  # noqa: E402
import route_check  # noqa: E402

try:  # the resolver and its registry ship in the development repository
    import resolver  # noqa: E402
except ImportError:  # pragma: no cover - packaged without the resolver
    resolver = None
try:  # er-core is development-only; without it critic enforcement is advisory-only (conservative)
    from er_core import engine as er_engine  # noqa: E402
    from er_core import schemas as er_schemas  # noqa: E402
except ImportError:  # pragma: no cover
    er_engine = er_schemas = None

VERSION = "1.3"
ROUTE, CLARIFY_GATE, FIELD_DESIGN = "ROUTE", "CLARIFY_GATE", "FIELD_DESIGN"
CAPABILITY_RESOLUTION, CAPABILITY_DISCOVERY, DESIGN_GATE = "CAPABILITY_RESOLUTION", "CAPABILITY_DISCOVERY", "DESIGN_GATE"
RUN_SPEC, G1_GATE, RUN_RESEARCH = "RUN_SPEC", "G1_GATE", "RUN_RESEARCH"
CRITIC_GATE, RUN_APPLY_CRITIC, G2_RESULT = "CRITIC_GATE", "RUN_APPLY_CRITIC", "G2_RESULT"
RUN_CRITIC_HANDOFF = "RUN_CRITIC_HANDOFF"
COMPLETE, STOPPED = "COMPLETE", "STOPPED"
STAGE_SKILL = {ROUTE: "problem-router", FIELD_DESIGN: "field-design-expert",
               CAPABILITY_RESOLUTION: "capability-resolver", CAPABILITY_DISCOVERY: "capability-resolver",
               RUN_SPEC: "engineering-research", RUN_RESEARCH: "engineering-research",
               RUN_APPLY_CRITIC: "engineering-research", RUN_CRITIC_HANDOFF: "engineering-research",
               CRITIC_GATE: "engineering-research-critic (fresh session, run by the human)"}
GATES = (CLARIFY_GATE, DESIGN_GATE, G1_GATE, CRITIC_GATE, G2_RESULT)
PRODUCT_STAGES = (RUN_RESEARCH, RUN_APPLY_CRITIC, RUN_CRITIC_HANDOFF)  # the only stages where product research may happen
G2_CONTINUE = ("ADDITIONAL_RESEARCH", "VERIFY_DIFFERENT_CANDIDATE")  # back to the RUN, SPEC and evidence kept
G2_TERMINAL = ("ACCEPT_NONE", "STOP")  # end with no recommendation (explicit human decision)
G2_DECISIONS = ("ADVANCE_TO_VERIFICATION",) + G2_CONTINUE + ("REOPEN_SPEC",) + G2_TERMINAL
ROUTE_MEANING = {"SELECTION_LED": "selection: the system is fixed, go straight to evidence-graded selection",
                 "DESIGN_LED": "design-led: the mechanism or architecture is open, design comes before any product",
                 "HYBRID": "hybrid: part of the system is fixed, but design decisions change what to buy",
                 "INSUFFICIENT_INPUT": "unclear: the physical objective is not yet clear enough to route"}
LABEL_TEXT = {1: "LEADER DISQUALIFIED - reopen CHECK",
              2: "LEADER NOT DISQUALIFIED, BUT HARD STATE CHANGED - reopen CHECK",
              3: "MATERIAL MISSED QUALIFYING CANDIDATE FOUND - reopen coverage",
              4: "LEADER SURVIVES AND NO MATERIAL MISSED QUALIFYING FAMILY FOUND - bounded result survives"}
# a capability need is a tool or skill; a missing value is an information gap for the design gate
INFORMATION_TAG = re.compile(r"-(data|measurement|measurements|value|values|input|inputs|requirement|requirements|answer)$")
OUT_OF_SCOPE = re.compile(r"out[ -]of[ -]scope|not in scope|outside (?:the )?scope|excluded", re.I)
QUANTITY = re.compile(r"(\d+(?:\.\d+)?)\s*([a-zA-Z%/]+(?:/[a-zA-Z]+)?)")


class Refused(Exception):
    """The artifact or answer is not allowed now; the state is unchanged."""


# ---------------------------------------------------------------- state

def new_state(statement: str) -> dict:
    if not statement.strip():
        raise Refused("the problem statement is empty")
    return {"artifact": "SELECTION_STATE", "version": VERSION, "statement": statement.strip(),
            "clarifications": [], "stage": ROUTE, "route": None, "route_artifact": None,
            "field_design": None, "handoff": None, "approved_handoff": None,
            "capabilities": {"needs": [], "known": [], "gaps": [], "decisions": {}, "approved_discovery": [],
                             "human": {}},
            "blockers": [], "acknowledged_unknowns": [], "out_of_scope": out_of_scope_items(statement),
            "run": {"session_id": None, "spec": None, "g1_approved": False, "g1_rows": None, "g1": None,
                    "check_result": None, "memo": None, "critic": None, "critic_skipped": False, "post_critic": None,
                    **copy.deepcopy(RUN_CONTINUATION)},
            "requirement_semantics": {"approved": [], "rejected": []},
            "open_gate": None, "gate_counter": 0, "history": [], "g2_decision": None, "g2_decisions": [],
            "critic_findings": [], "critic_caveats": [], "final": None}


# G2 continuation bookkeeping (selector 1.2); setdefault keeps 1.1 state files readable
RUN_CONTINUATION = {"round": 1, "rounds": [], "continuation": None, "min_check_version": 0, "advance_target": None}


def upgrade(s: dict) -> dict:
    for k, v in RUN_CONTINUATION.items():
        s["run"].setdefault(k, copy.deepcopy(v))
    s.setdefault("g2_decisions", [])
    s.setdefault("critic_findings", [])
    s.setdefault("critic_caveats", [])
    s.setdefault("final", None)
    return s


def effective_statement(state: dict) -> str:
    """The statement plus every human answer, so quotes from either are valid user words."""
    parts = [state["statement"]]
    for c in state["clarifications"]:
        parts.append(f"Additional information from the user ({c['gate']}): {c['text']}")
    return "\n\n".join(parts)


def out_of_scope_items(statement: str) -> list[dict]:
    """User sentences that put something out of scope, with the quantities they name."""
    items = []
    for sentence in re.split(r"(?<=[.;!?])\s+|\n+", statement):
        if OUT_OF_SCOPE.search(sentence):
            items.append({"quote": sentence.strip(), "quantities": [norm_q(v, u) for v, u in QUANTITY.findall(sentence)]})
    return items


def norm_q(value, unit) -> str:
    return f"{float(value):g} {unit.lower()}"


def quantities(text) -> set:
    return {norm_q(v, u) for v, u in QUANTITY.findall(str(text))}


def log(state, event, detail):
    state["history"].append({"stage": state["stage"], "event": event, "detail": detail})


def open_gate(state, stage, payload):
    state["gate_counter"] += 1
    state["stage"] = stage
    state["open_gate"] = {"id": f"GATE-{state['gate_counter']}-{stage}", "stage": stage, **payload}


def require_stage(state, *stages, what):
    if state["stage"] not in stages:
        raise Refused(f"{what} is not allowed at stage {state['stage']}; expected {' or '.join(stages)}")


# ---------------------------------------------------------------- capabilities

def known_capability(tag: str) -> str | None:
    """A usable registry entry that covers the tag, or None. Exact tag match, as the resolver does."""
    if resolver is None:
        return None
    try:
        registry = resolver.load_registry()
    except (OSError, ValueError):
        return None
    for e in registry.get("entries", []):
        if e.get("status") in resolver.USABLE_STATUSES and tag in (e.get("capabilities") or []):
            return e["id"]
    return None


def classify_needs(needs: list) -> tuple[list, list, list]:
    known, gaps, problems = [], [], []
    for n in needs:
        tag = str(n.get("tag", ""))
        if INFORMATION_TAG.search(tag):
            problems.append(f"capability need {tag!r} is an information gap (a missing value), not a missing "
                            "capability: list it as an unresolved requirement for the design gate")
            continue
        entry = known_capability(tag)
        (known if entry else gaps).append({"tag": tag, "why": n.get("why", ""), **({"entry": entry} if entry else {})})
    return known, gaps, problems


def external_sources(request: dict) -> list:
    sources = ((request or {}).get("search_record") or {}).get("sources") or []
    return [s for s in sources if not str(s).startswith("manual:")]


# ---------------------------------------------------------------- record artifacts

def record(state: dict, artifact: dict) -> dict:
    """Record a skill's artifact at the current stage and advance. Raises Refused; never mutates on refusal."""
    s = upgrade(copy.deepcopy(state))
    if not isinstance(artifact, dict):
        raise Refused("the artifact is not a JSON object")
    kind = artifact.get("artifact") or artifact.get("artifact_type") or (
        "CAPABILITY_RESOLUTION" if "CAPABILITY_DECISION" in artifact else None)
    handler = {"PROBLEM_ROUTE": _route, "FIELD_DESIGN": _field_design, "FIELD_DESIGN_RESULT": _field_design_only,
               "CAPABILITY_RESOLUTION": _capability, "RUN_STOP": _run_stop, "CRITIC_RESULT": _critic,
               "SPEC": _product_artifact, "CHECK_RESULT": _product_artifact, "EVIDENCE_TABLE": _product_artifact,
               "ENGINEERING_RESEARCH_HANDOFF": _field_design_only}.get(kind)
    if handler is None:
        raise Refused(f"unknown artifact {kind!r}")
    try:
        handler(s, artifact)
    except (KeyError, TypeError, AttributeError, IndexError) as exc:
        raise Refused(f"{kind} is malformed (missing or invalid field {exc}); record it in its skill's format")
    return s


def _route(s, route):
    require_stage(s, ROUTE, what="a PROBLEM_ROUTE")
    problems = route_check.check_route(route, effective_statement(s))
    if problems:
        raise Refused("PROBLEM_ROUTE fails route_check: " + "; ".join(problems))
    s["route"], s["route_artifact"] = route["route"], route
    log(s, "PROBLEM_ROUTE", route["route"])
    if route["route"] == "INSUFFICIENT_INPUT":
        questions = [m["item"] for m in route["missing_inputs"] if m.get("blocks_routing")] or \
                    ["What physical result is wanted (what must move, flow, be measured, protected or held)?"]
        open_gate(s, CLARIFY_GATE, {"questions": questions,
                                    "options": ["ANSWER (text with the missing facts)", "STOP"]})
    elif route["route"] == "SELECTION_LED":
        s["stage"] = RUN_SPEC
    else:
        s["stage"] = FIELD_DESIGN


def _field_design_only(s, _artifact):
    raise Refused("record FIELD_DESIGN_RESULT and ENGINEERING_RESEARCH_HANDOFF together as "
                  '{"artifact": "FIELD_DESIGN", "result": {...}, "handoff": {...}}')


def _field_design(s, art):
    if s["route"] == "SELECTION_LED":
        raise Refused("a SELECTION_LED problem is not redesigned: no Field/Design Expert stage")
    require_stage(s, FIELD_DESIGN, what="a Field/Design Expert result")
    result, handoff = art.get("result"), art.get("handoff")
    statement = effective_statement(s)
    problems = [f"RESULT: {p}" for p in fde_check.check_result(result, statement)] + \
               [f"HANDOFF: {p}" for p in fde_check.check_handoff(handoff, statement)]
    if not problems and handoff.get("status") != "DRAFT_PENDING_HUMAN_GATE":
        problems.append("HANDOFF: the expert's handoff is a DRAFT; only the design gate approves it")
    problems += scope_problems(s, handoff) if isinstance(handoff, dict) else []
    known, gaps, cap_problems = classify_needs(fde_check._list(result, "capability_needs") if isinstance(result, dict) else [])
    problems += cap_problems
    if problems:
        raise Refused("Field/Design Expert output fails its checks: " + "; ".join(problems))
    s["field_design"], s["handoff"] = result, handoff
    s["capabilities"].update(needs=result["capability_needs"], known=known, gaps=gaps)
    s["blockers"] = selection_blockers(result, handoff)
    log(s, "FIELD_DESIGN", {"known_capabilities": [k["tag"] for k in known], "gaps": [g["tag"] for g in gaps]})
    if any(g["tag"] not in s["capabilities"]["decisions"] for g in gaps):
        s["stage"] = CAPABILITY_RESOLUTION
    else:
        design_gate(s)


def selection_blockers(result, handoff) -> list[str]:
    """UNKNOWN first-order variables and UNKNOWN requirements: the selection cannot rest on them silently."""
    out = [v["variable"] for v in fde_check._list(result, "first_order_variables")
           if isinstance(v, dict) and v.get("current_value", "UNKNOWN") == "UNKNOWN"]
    out += [u["parameter"] for u in fde_check._list(result, "unresolved_requirements") if isinstance(u, dict)]
    out += [u["parameter"] for u in fde_check._list(handoff, "unknown_requirements") if isinstance(u, dict)]
    seen, unique = set(), []
    for b in out:
        if fde_check.norm(b) not in seen:
            seen.add(fde_check.norm(b))
            unique.append(b)
    return unique


def scope_problems(s, handoff) -> list[str]:
    """A quantity the user put out of scope never becomes a requirement or an in-scope item."""
    problems = []
    banned = {q for item in s["out_of_scope"] for q in item["quantities"]}
    if not banned:
        return problems
    for r in fde_check._list(handoff, "hard_requirements"):
        if isinstance(r, dict) and quantities(f"{r.get('value', '')} {r.get('unit', '')}") & banned:
            problems.append(f"HANDOFF: HARD requirement {r.get('id')} uses an out-of-scope value "
                            f"({', '.join(sorted(quantities(str(r.get('value', '')) + ' ' + str(r.get('unit', ''))) & banned))})")
    for r in fde_check._list(handoff, "reference_values"):
        if isinstance(r, dict) and quantities(f"{r.get('value', '')} {r.get('unit', '')}") & banned:
            problems.append(f"HANDOFF: reference value {r.get('parameter')!r} carries an out-of-scope value; "
                            "out-of-scope items belong in approved_search_scope.out_of_scope only")
    scope = handoff.get("approved_search_scope") if isinstance(handoff.get("approved_search_scope"), dict) else {}
    for item in scope.get("in_scope") or []:
        if quantities(item) & banned:
            problems.append(f"HANDOFF: in_scope item {item!r} names an out-of-scope value")
    listed = quantities(" ".join(map(str, scope.get("out_of_scope") or [])))
    for q in sorted(banned - listed):
        problems.append(f"HANDOFF: the user put {q} out of scope; approved_search_scope.out_of_scope must say so")
    return problems


def _capability(s, art):
    require_stage(s, CAPABILITY_RESOLUTION, CAPABILITY_DISCOVERY, what="a capability resolution")
    request = art.get("request")
    decision = (art.get("CAPABILITY_DECISION") and art) or art.get("decision")
    if not isinstance(request, dict) or not isinstance(decision, dict):
        raise Refused('record a capability resolution as {"artifact": "CAPABILITY_RESOLUTION", '
                      '"request": {...}, "decision": {"CAPABILITY_DECISION": {...}}}')
    tags = request.get("required_capabilities") or []
    gap_tags = {g["tag"] for g in s["capabilities"]["gaps"]}
    if not tags or not set(tags) <= gap_tags:
        raise Refused(f"the Capability Resolver runs only for genuine capability gaps {sorted(gap_tags) or '[]'}; "
                      f"request names {tags}")
    external = external_sources(request)
    if external and s["stage"] != CAPABILITY_DISCOVERY:
        raise Refused("external discovery evidence is not allowed before a human approves discovery at the design gate")
    if external and not set(tags) <= set(s["capabilities"]["approved_discovery"]):
        raise Refused(f"external discovery for {tags} was not approved by the human")
    if resolver is None:
        raise Refused("the capability resolver is not available; resolve the gap by hand at the design gate")
    try:
        registry = resolver.load_registry()
        problems = resolver.verify_decision(decision, request, registry)
    except (OSError, ValueError) as exc:  # normalize_request refuses ungated external evidence (GA-01)
        raise Refused(f"capability request refused by the resolver: {exc}")
    if problems:
        raise Refused("CAPABILITY_DECISION does not match the resolver: " + "; ".join(problems))
    d = decision["CAPABILITY_DECISION"]
    for t in tags:
        s["capabilities"]["decisions"][t] = {"decision": d["decision"], "recommended": d.get("recommended", []),
                                             "human_approval_required": d.get("human_approval_required"),
                                             "external_discovery": bool(external)}
    log(s, "CAPABILITY_DECISION", {"tags": tags, "decision": d["decision"]})
    if all(g["tag"] in s["capabilities"]["decisions"] for g in s["capabilities"]["gaps"]):
        design_gate(s)


def design_gate(s):
    caps = s["capabilities"]
    items = []
    for g in caps["gaps"]:
        d = caps["decisions"].get(g["tag"], {})
        if d.get("decision") == "SEARCH_REQUIRED":
            items.append(f"{g['tag']}: nothing known covers it; approve read-only external discovery, or defer")
        elif d:
            items.append(f"{g['tag']}: resolver says {d['decision']} {', '.join(d.get('recommended') or [])}".rstrip()
                         + "; approve it (you install or connect it yourself), or defer")
    open_gate(s, DESIGN_GATE, {
        "blockers": s["blockers"], "capability_items": items,
        "recommendation": ("RESOLVE_FIRST: the selection would rest on unknown first-order values"
                           if s["blockers"] else "READY: approve the handoff to start selection"),
        "options": ["APPROVE_HANDOFF (acknowledge every unknown you accept, or 'ALL')",
                    "SUPPLY_INFORMATION (text: measured or decided values; the design stage reruns)",
                    "APPROVE_DISCOVERY (capability gap tags)", "STOP"]})


def _run_stop(s, art):
    stop = art.get("stop")
    run = s["run"]
    if s["route"] in ("DESIGN_LED", "HYBRID") and s["approved_handoff"] is None:
        raise Refused(f"{s['route']}: no product research or RUN stage before the design gate approves the handoff")
    if s["route"] is None:
        raise Refused("route the problem first")
    if stop == "G1":
        require_stage(s, RUN_SPEC, what="a RUN stop at G1")
        if art.get("check_result") or (art.get("memo") or {}).get("shortlist"):
            raise Refused("product research before G1 approval: a G1 stop carries the SPEC only")
        spec = art.get("spec")
        if not isinstance(spec, dict) or not spec.get("requirements"):
            raise Refused("a G1 stop needs the draft SPEC with its requirements")
        if order_problem(spec):
            raise Refused(order_problem(spec))
        rows = G1.classify_spec(spec, effective_statement(s), human_approvals(s))
        rejected = {r["signature"]: r["ref"] for r in semantics(s)["rejected"]}
        again = [f"{r['id']} ({r['text']}, rejected at {rejected[r['signature']]})" for r in rows
                 if r["class"] == "HARD" and r["signature"] in rejected]
        if again:
            raise Refused("the draft SPEC repeats HARD constraints the human rejected at G1: " + "; ".join(again))
        run.update(spec=spec, g1_rows=rows, session_id=art.get("run_session_id") or run["session_id"])
        log(s, "RUN_STOP", "G1 " + ", ".join(f"{r['id']} {r['semantic']}" for r in rows))
        open_gate(s, G1_GATE, {
            "requirements": [{k: r[k] for k in ("id", "class", "semantic", "text", "reason")} for r in rows],
            "decisions_needed": [r["id"] for r in rows if r["semantic"] == G1.PROPOSED],
            "unknowns": [r["id"] for r in rows if r["semantic"] == G1.UNKNOWN],
            "options": ["APPROVE_SPEC (requirement_decisions: APPROVE or REJECT for every "
                        "PROPOSED_ENGINEERING_CONSTRAINT; acknowledged_unknowns: every UNKNOWN row, or 'ALL')",
                        "CHANGE_SPEC (text)", "STOP"]})
        return
    if stop not in ("CRITIC_HANDOFF", "G2"):
        raise Refused("RUN_STOP.stop must be G1, CRITIC_HANDOFF or G2")
    if not run["g1_approved"]:
        raise Refused("product research before G1 approval is not allowed")
    require_stage(s, RUN_RESEARCH, RUN_APPLY_CRITIC, RUN_CRITIC_HANDOFF, what=f"a RUN stop at {stop}")
    spec, check, memo = art.get("spec") or run["spec"], art.get("check_result"), art.get("memo")
    problems = []
    if not isinstance(memo, dict):
        problems.append("a RUN stop after G1 needs its memo summary")
    if not isinstance(check, dict):
        problems.append("a RUN stop after G1 needs the CHECK_RESULT")
    if er_schemas is not None:
        for a in (spec, check):
            if isinstance(a, dict) and a.get("artifact_type"):
                problems += [f"{a['artifact_type']}: {e}" for e in er_schemas.schema_errors(a)]
    if isinstance(spec, dict):
        problems += [f"G1 semantics: {p}" for p in G1.post_g1_problems(spec, run.get("g1"))]
        problems += [order_problem(spec)] if order_problem(spec) else []
    if problems:
        raise Refused("; ".join(problems))
    cands = {c["candidate_id"]: c for c in check.get("candidates", [])}
    preferred = memo.get("preferred")
    if preferred is not None and preferred not in cands:
        raise Refused(f"memo.preferred {preferred!r} is not a candidate of the CHECK_RESULT")
    if s["stage"] == RUN_CRITIC_HANDOFF:  # ADVANCE_TO_VERIFICATION without a critic PASS: the leader goes to the critic
        target = run["advance_target"]
        if stop != "CRITIC_HANDOFF" or preferred != target:
            raise Refused(f"ADVANCE_TO_VERIFICATION sends {target!r} to the independent critic: record the RUN's "
                          f"CRITIC_HANDOFF stop with memo.preferred {target!r}")
        if check.get("version", 0) < (run["check_result"] or {}).get("version", 0):
            raise Refused("the critic handoff must carry the latest CHECK_RESULT (not a superseded version)")
        run.update(spec=spec, check_result=check, memo=memo, session_id=art.get("run_session_id") or run["session_id"])
        log(s, "RUN_STOP", f"CRITIC_HANDOFF (advance {target} to verification, round {run['round']})")
        open_gate(s, CRITIC_GATE, {"options": ["run engineering-research-critic in a FRESH session on the "
                                               "CRITIC_BRIEF and record its CRITIC_RESULT", "SKIP_CRITIC (explicit)", "STOP"]})
        return
    if s["stage"] == RUN_RESEARCH and run["min_check_version"] and check.get("version", 0) <= run["min_check_version"]:
        raise Refused(f"the RUN was resumed at G2 ({run['continuation']['decision']}): record the re-evaluation as "
                      f"CHECK_RESULT_v{run['min_check_version'] + 1} or later; CHECK_RESULT_v{check.get('version', 0)} "
                      "is the superseded result (no silent loop)")
    if s["stage"] == RUN_RESEARCH:
        if stop == "CRITIC_HANDOFF":
            if preferred is None:
                raise Refused("a critic handoff needs a preferred candidate")
            run.update(spec=spec, check_result=check, memo=memo, session_id=art.get("run_session_id") or run["session_id"])
            log(s, "RUN_STOP", "CRITIC_HANDOFF")
            open_gate(s, CRITIC_GATE, {"options": ["run engineering-research-critic in a FRESH session on the "
                                                   "CRITIC_BRIEF and record its CRITIC_RESULT", "SKIP_CRITIC (explicit)", "STOP"]})
            return
        if preferred is not None and not run["critic_skipped"]:
            raise Refused("the memo names a preferred candidate: it must go to the independent critic before G2")
        run.update(spec=spec, check_result=check, memo=memo)
        log(s, "RUN_STOP", "G2 (no critic: " + ("skipped by the human" if run["critic_skipped"] else "no preferred candidate") + ")")
        g2_gate(s)
        return
    # RUN_APPLY_CRITIC: the RUN applied the CRITIC_RESULT
    if stop != "G2":
        raise Refused("after the critic the RUN applies CRITIC_RESULT and stops at G2")
    critic = run["critic"]
    if memo.get("critic_applied") is not True:
        raise Refused("the RUN must apply the CRITIC_RESULT before G2 (memo.critic_applied true)")
    label = critic["label"]
    consumed = critic["consumed_check_result_version"]
    if label in (1, 2, 3) and check.get("version", 0) <= consumed:
        raise Refused(f"critic label {label} reopened the result: G2 needs CHECK_RESULT_v{consumed + 1} or later "
                      "(the superseded result cannot become final)")
    if label == 1 and preferred == critic["leader"]:
        raise Refused(f"critic label 1 disqualified {critic['leader']!r}; it cannot stay the preferred candidate")
    if label == 1 and preferred is not None and cands.get(preferred, {}).get("lane") == "EXCLUDED":
        raise Refused(f"preferred candidate {preferred!r} is EXCLUDED")
    findings = [f for f in s["critic_findings"] if f["critic_pass"] == critic["pass"]]
    mapping = memo.get("critic_candidate_ids") or {}
    problems = []
    for f in findings:
        if f["kind"] == M.MISSED:
            cid, problem = M.match_candidate(f["candidate_name"], check.get("candidates") or [],
                                             mapping.get(f["id"]) or mapping.get(f["candidate_name"]))
            if problem:
                problems.append(f"{f['id']}: {problem}; the RUN adds the critic's candidate to the CHECK_RESULT "
                                "(map it in memo.critic_candidate_ids if the names differ)")
            f["candidate_id"] = cid
    found, caveats, limits = M.concerns(memo, critic["pass"], run["round"], critic["leader"], critic["fired"])
    for f in list(found):
        if f["target"]:
            cid, problem = M.match_candidate(f["target"], check.get("candidates") or [],
                                             f["target"] if f["target"] in cands else None)
            if problem:
                problems.append(f"concern {f['id']}: {problem} (memo.critic_concerns[].candidate is a candidate_id)")
            f["candidate_id"] = cid
            # missing evidence on a candidate that is not evidence-qualified (the critic's C3 did not fire on it):
            # bounded coverage, recorded; under the RUN's lanes it cannot be preferred without new evidence
            if cid and cid != preferred and cands[cid].get("lane") != "SPECIFY NOW" \
                    and f["concern_type"] in ("EVIDENCE_QUALITY", "PROVENANCE"):
                found.remove(f)
                limits.append({**{k: f[k] for k in ("critic_pass", "round", "leader", "id", "concern_type", "candidate",
                                                     "candidate_id", "summary", "quote")},
                               "disposition": f"COVERAGE_LIMITATION ({cid} is {cands[cid].get('lane')})"})
    s["critic_findings"] += found
    problems += soft_value_problems(s, spec, memo)
    if problems:
        raise Refused("; ".join(problems))
    s["critic_caveats"] += caveats + limits
    if caveats or limits:
        log(s, "CRITIC_CAVEATS", [{"id": c["id"], "type": c["concern_type"], "disposition": c["disposition"],
                                   "quote": c["quote"]} for c in caveats + limits])
    run["post_critic"] = {"check_result": check, "memo": memo}
    log(s, "RUN_STOP", f"G2 after critic label {label}")
    g2_gate(s)


def order_problem(spec) -> str | None:
    """The RUN's SPEC contract states soft_priority_order; with two or more SOFT rows it cannot be assumed."""
    soft = [r.get("id") for r in spec.get("requirements") or [] if isinstance(r, dict) and G1.row_class(r) == "SOFT"]
    if len(soft) > 1 and not spec.get("soft_priority_order"):
        return (f"the SPEC has SOFT rows {', '.join(map(str, soft))} but no soft_priority_order: record the RUN's "
                "SPEC soft_priority_order (the ranking order the human approves at G1) as it is")
    return None


def soft_value_problems(s, spec, memo) -> list:
    """memo.soft_values must give every ranking criterion for the leader and each missed candidate (UNKNOWN allowed)."""
    crits, _ = M.ranking(spec, s["run"].get("g1"), effective_statement(s))
    preferred = memo.get("preferred")
    missed = [f["candidate_id"] for f in s["critic_findings"] if f["kind"] in (M.MISSED, M.CONCERN) and f.get("candidate_id")
              and f["candidate_id"] != preferred]
    if not crits or preferred is None or not missed:
        return []
    values = memo.get("soft_values")
    if not isinstance(values, dict):
        return ["after a critic the memo needs soft_values {candidate_id: {criterion: {value, unit, source}}} for the "
                "leader and every missed candidate (value UNKNOWN where the RUN has none)"]
    problems = []
    for cid in dict.fromkeys([preferred] + missed):
        for c in crits:
            v = (values.get(cid) or {}).get(c["id"])
            if v is None:
                problems.append(f"memo.soft_values has no {c['id']} for {cid} (write value UNKNOWN if the RUN has none)")
            elif isinstance(v, dict) and str(v.get("value", "")).strip().upper() not in ("", "UNKNOWN") \
                    and not (v.get("source") or v.get("authority")):
                problems.append(f"memo.soft_values {cid} {c['id']} = {v.get('value')} has no source")
    return problems


def current(run) -> tuple[dict, dict]:
    """The latest CHECK_RESULT and memo: the RUN's post-critic re-check if there is one."""
    final = run["post_critic"] or {"check_result": run["check_result"], "memo": run["memo"]}
    return final["check_result"] or {}, final["memo"] or {}


def critic_on_leader(run) -> bool:
    """The current critic pass attacked the current leader and the RUN applied it (not skipped)."""
    _, memo = current(run)
    c = run["critic"]
    return bool(c and run["post_critic"] and not run["critic_skipped"]
                and memo.get("preferred") is not None and c["leader"] == memo["preferred"])


def critic_pass(run) -> bool:
    """A critic PASS for the current leader: label 4 on that leader, applied by the RUN, not skipped."""
    return critic_on_leader(run) and run["critic"]["label"] == 4


def reassess(s) -> list:
    """Classify every recorded critic finding against the current leader and CHECK_RESULT (materiality gate).
    The current pass first (its own findings can never be settled by itself), then every earlier finding."""
    run = s["run"]
    check, memo = current(run)
    c = run["critic"] if critic_on_leader(run) else None
    ctx = {"check": check, "leader": memo.get("preferred"), "spec": run["spec"] or {},
           "soft_values": memo.get("soft_values") or {}, "pass_no": c["pass"] if c else 0,
           "ranking": M.ranking(run["spec"] or {}, run.get("g1"), effective_statement(s)), "clean_pass_on_leader": False}
    mine = [f for f in s["critic_findings"] if c and f["critic_pass"] == c["pass"]]
    for f in mine:
        f["class"], f["status"], f["reasons"] = M.assess(f, ctx)
    ctx["clean_pass_on_leader"] = bool(c) and c["label"] in (3, 4) and all(f["status"] == M.NON_MATERIAL for f in mine)
    for f in s["critic_findings"]:
        if not any(f is m for m in mine):
            f["class"], f["status"], f["reasons"] = M.assess(f, ctx)
    entries = []
    for f in s["critic_findings"]:
        f["assessments"].append({"round": run["round"], "check_result_version": check.get("version"),
                                 "leader": ctx["leader"], "class": f["class"], "status": f["status"], "reasons": f["reasons"]})
        entries.append({"id": f["id"], "kind": f["kind"], "candidate": f.get("candidate_id") or f.get("candidate")
                        or f.get("candidate_name"), "class": f["class"], "status": f["status"], "reasons": f["reasons"]})
    if entries:
        log(s, "CRITIC_MATERIALITY", {"round": run["round"], "check_result_version": check.get("version"),
                                      "leader": ctx["leader"], "critic_pass": ctx["pass_no"] or None, "findings": entries})
    return entries


def open_findings(s) -> list:
    return [f for f in s["critic_findings"] if f.get("status") in (M.MATERIAL, M.INSUFFICIENT)]


def critic_clear(s) -> bool:
    """Final is allowed: the leader's own critic pass is clean (label 4, or label 3 with every finding
    NON_MATERIAL), the RUN applied it, and no MATERIAL or INSUFFICIENT_EVIDENCE finding is open."""
    run = s["run"]
    return critic_on_leader(run) and run["critic"]["label"] in (3, 4) and not open_findings(s)


def run_must_address(s) -> list:
    """Open findings a new critic pass cannot settle: about a candidate that is not the leader (a missed
    candidate, or a concern about another candidate), so the RUN must research or re-rank first."""
    _, memo = current(s["run"])
    return [f for f in open_findings(s) if (f["kind"] == M.MISSED or (f["kind"] == M.CONCERN and f.get("candidate_id")))
            and f.get("candidate_id") != memo.get("preferred")]


def finding_line(f) -> str:
    return f"{f['id']} {f['kind']} {f.get('candidate_id') or f.get('candidate_name') or f.get('candidate')}: " \
           f"{f['status']} ({'; '.join(f.get('reasons') or [])})"


def g2_gate(s):
    run = s["run"]
    _, memo = current(run)
    preferred = memo.get("preferred")
    reassess(s)
    clear, blocking = critic_clear(s), run_must_address(s)
    basis = ("critic PASS" if critic_pass(run) else "critic label 3, every finding NON_MATERIAL or resolved")
    advance = ("ADVANCE_TO_VERIFICATION: " + (f"finalize {preferred} ({basis})" if clear else
               "not available (open critic findings the RUN must address: "
               + ", ".join(f["id"] for f in blocking) + ")" if preferred and blocking else
               f"send {preferred} to the independent critic first (no clean critic pass yet)" if preferred else
               "not available (no preferred candidate)"))
    open_gate(s, G2_RESULT, {
        "round": run["round"], "preferred": preferred, "critic_pass": critic_pass(run), "critic_clear": clear,
        "critic_findings": [{"id": f["id"], "kind": f["kind"], "critic_pass": f["critic_pass"],
                             "candidate": f.get("candidate_id") or f.get("candidate_name") or f.get("candidate"),
                             "class": f["class"], "status": f["status"], "reasons": f["reasons"]}
                            for f in s["critic_findings"]],
        "open_findings": [f["id"] for f in open_findings(s)],
        "run_must_address": [f["id"] for f in blocking],
        "options": [advance, "ADDITIONAL_RESEARCH (text: what to research; back to the RUN, SPEC and evidence kept)",
                    "VERIFY_DIFFERENT_CANDIDATE (candidates and/or text; back to the RUN, SPEC kept)",
                    "REOPEN_SPEC (text: what changes; back to G1, explicit approval again)",
                    "ACCEPT_NONE (end with no recommendation)", "STOP"]})


def _product_artifact(s, art):
    if s["stage"] not in PRODUCT_STAGES:
        raise Refused(f"{art.get('artifact_type')} is product research; it is allowed only in the RUN stage after "
                      f"G1 approval (now {s['stage']}). Record it inside a RUN_STOP")
    raise Refused("record RUN artifacts inside a RUN_STOP")


def _critic(s, critic):
    require_stage(s, CRITIC_GATE, what="a CRITIC_RESULT")
    run = s["run"]
    problems = []
    if er_schemas is not None:
        problems += er_schemas.schema_errors(critic)
    if problems:
        raise Refused("CRITIC_RESULT is invalid: " + "; ".join(problems))
    ind = critic.get("independence") or {}
    if ind.get("session_independence") != "FRESH_SESSION":
        problems.append("the critic must run in a fresh session (session_independence FRESH_SESSION)")
    if run["session_id"] and critic.get("critic_session_id") == run["session_id"]:
        problems.append("the critic session is the RUN session: not independent")
    if ind.get("independence_quality") in ("INSUFFICIENT", "UNKNOWN"):
        problems.append(f"critic independence_quality {ind.get('independence_quality')}")
    if critic.get("job1", {}).get("leader") != run["memo"].get("preferred"):
        problems.append("the critic attacked a different leader than the memo's preferred candidate")
    if problems:
        raise Refused("CRITIC_RESULT not accepted: " + "; ".join(problems))
    if er_engine is not None:
        enf = er_engine.critic_enforcement(run["spec"], run["check_result"], critic)
        violations = [p for p in enf["problems"] if p["severity"] == "violation"]
        if violations:
            raise Refused("CRITIC_RESULT fails er-core enforcement: " + "; ".join(p["message"] for p in violations))
        label, basis = enf["primary_outcome_label"], "er-core computed"
        fired = [c for c in ("C1", "C2", "C3") if enf[c]]
    else:  # fail closed: any advisory C1-C3 or a label other than 4 reopens the result
        fired = [c for c in ("C1", "C2", "C3") if critic.get(c) == "YES"]
        label = critic["advisory_outcome_label"]["number"]
        if label == 4 and fired:
            label = 2 if {"C1", "C2"} & set(fired) else 3
        basis = "advisory only (er-core unavailable)"
    pass_no = sum(1 for h in s["history"] if h["event"] == "CRITIC_RESULT") + 1
    findings = M.extract(critic, run["spec"], fired, label, pass_no, run["round"])
    s["critic_findings"] += findings
    run["critic"] = {"label": label, "text": LABEL_TEXT[label], "basis": basis, "fired": fired, "pass": pass_no,
                     "finding_ids": [f["id"] for f in findings], "critic_session_id": critic.get("critic_session_id"),
                     "job1_no_hard_status_change": not (critic["job1"].get("findings") or []),
                     "job1_documents_examined": critic["job1"].get("documents_examined") or [],
                     "leader_evidence_authorities": sorted({str(e.get("authority", "")) for e in critic.get("evidence") or []
                                                            if isinstance(e, dict) and (e.get("primary_run") or str(e.get("id"))
                                                            in map(str, critic["job1"].get("documents_examined") or []))}),
                     "advisory_label": critic["advisory_outcome_label"]["number"], "leader": critic["job1"]["leader"],
                     "consumed_check_result_version": critic["consumed_check_result_version"],
                     "independence_quality": ind.get("independence_quality"), "critic_family": critic.get("critic_family")}
    log(s, "CRITIC_RESULT", f"label {label} ({basis}), pass {pass_no}")
    if findings:
        log(s, "CRITIC_FINDINGS", [{"id": f["id"], "kind": f["kind"], "summary": f["summary"]} for f in findings])
    s["open_gate"] = None
    s["stage"] = RUN_APPLY_CRITIC


# ---------------------------------------------------------------- human answers

def answer(state: dict, ans: dict) -> dict:
    s = upgrade(copy.deepcopy(state))
    gate = s["open_gate"]
    if not gate:
        raise Refused(f"no human gate is open at stage {s['stage']}")
    if ans.get("gate") != gate["id"]:
        raise Refused(f"the answer is for {ans.get('gate')!r}; the open gate is {gate['id']}")
    decision = ans.get("decision")
    if decision == "STOP" and gate["stage"] != G2_RESULT:
        log(s, "HUMAN", f"{gate['id']}: STOP")
        s["open_gate"], s["stage"] = None, STOPPED
        return s
    stage = gate["stage"]
    if stage == CLARIFY_GATE:
        if decision != "ANSWER" or not str(ans.get("text", "")).strip():
            raise Refused("the clarify gate takes ANSWER with the missing facts as text, or STOP")
        s["clarifications"].append({"gate": gate["id"], "text": ans["text"].strip()})
        s["out_of_scope"] = out_of_scope_items(effective_statement(s))
        s["route"], s["route_artifact"], s["open_gate"], s["stage"] = None, None, None, ROUTE
    elif stage == DESIGN_GATE:
        _design_answer(s, gate, decision, ans)
    elif stage == G1_GATE:
        if decision == "APPROVE_SPEC":
            _g1_approve(s, gate, ans)
        elif decision == "CHANGE_SPEC" and str(ans.get("text", "")).strip():
            s["clarifications"].append({"gate": gate["id"], "text": ans["text"].strip()})
            s["open_gate"], s["stage"] = None, RUN_SPEC
        else:
            raise Refused("G1 takes APPROVE_SPEC, CHANGE_SPEC with text, or STOP (silence is not approval)")
    elif stage == CRITIC_GATE:
        if decision != "SKIP_CRITIC":
            raise Refused("the critic gate takes a recorded CRITIC_RESULT, SKIP_CRITIC, or STOP")
        s["run"]["critic_skipped"] = True
        s["open_gate"], s["stage"] = None, RUN_RESEARCH
    elif stage == G2_RESULT:
        _g2_answer(s, gate, decision, ans)
        return s
    log(s, "HUMAN", f"{gate['id']}: {decision}")
    return s


def _g2_answer(s, gate, decision, ans):
    """G2 transitions (selector 1.2). Only a critic PASS or an explicit human stop is terminal."""
    if decision not in G2_DECISIONS:
        raise Refused(f"G2 takes one of {G2_DECISIONS}")
    run = s["run"]
    check, memo = current(run)
    preferred = memo.get("preferred")
    text = str(ans.get("text", "")).strip()
    targets = [str(c) for c in ans.get("candidates") or []]
    if decision == "ADVANCE_TO_VERIFICATION" and preferred is None:
        raise Refused("ADVANCE_TO_VERIFICATION needs a preferred candidate and there is none; choose "
                      "ADDITIONAL_RESEARCH, VERIFY_DIFFERENT_CANDIDATE, REOPEN_SPEC, ACCEPT_NONE or STOP")
    blocking = run_must_address(s)
    if decision == "ADVANCE_TO_VERIFICATION" and blocking:
        raise Refused("ADVANCE_TO_VERIFICATION is blocked by open critic findings the RUN must address first: "
                      + "; ".join(finding_line(f) for f in blocking)
                      + ". Choose ADDITIONAL_RESEARCH, VERIFY_DIFFERENT_CANDIDATE, REOPEN_SPEC, ACCEPT_NONE or STOP")
    if decision == "VERIFY_DIFFERENT_CANDIDATE" and not (targets or text):
        raise Refused("VERIFY_DIFFERENT_CANDIDATE needs the candidate(s) to verify (candidates, or text)")
    if decision == "REOPEN_SPEC" and not text:
        raise Refused("REOPEN_SPEC needs the SPEC change as text (the human's own words)")
    record_ = {"gate": gate["id"], "decision": decision, "text": text, "round": run["round"],
               **({"candidates": targets} if targets else {})}
    s["g2_decision"] = record_
    s["g2_decisions"].append(record_)
    passed = critic_clear(s)
    if decision == "ADVANCE_TO_VERIFICATION" and passed:
        s["final"] = {"basis": "CRITIC_PASS" if run["critic"]["label"] == 4 else "CRITIC_FINDINGS_NON_MATERIAL",
                      "gate": gate["id"], "preferred": preferred, "critic_pass_no": run["critic"]["pass"],
                      "check_result_version": check.get("version"), "critic_label": run["critic"]["label"],
                      "critic_findings": {f["id"]: f["status"] for f in s["critic_findings"]}}
        to = COMPLETE
    elif decision in G2_TERMINAL:
        s["final"] = {"basis": "HUMAN_STOP_NO_RECOMMENDATION", "gate": gate["id"], "decision": decision,
                      "critic_pass_withheld": preferred if passed else None}
        to = COMPLETE
    else:
        archive_round(s, record_)
        run["critic"], run["post_critic"], run["critic_skipped"], run["advance_target"] = None, None, False, None
        run["check_result"], run["memo"] = check or None, memo or None
        if decision == "ADVANCE_TO_VERIFICATION":
            run["advance_target"], run["min_check_version"] = preferred, 0
            to = RUN_CRITIC_HANDOFF
        elif decision in G2_CONTINUE:
            run["min_check_version"] = check.get("version", 0)
            to = RUN_RESEARCH
        else:  # REOPEN_SPEC: back to G1; research needs a new explicit APPROVE_SPEC
            s["clarifications"].append({"gate": gate["id"], "text": text})
            s["out_of_scope"] = out_of_scope_items(effective_statement(s))
            run["min_check_version"] = check.get("version", 0)
            run.update(g1_approved=False, g1=None, g1_rows=None, check_result=None, memo=None)
            to = RUN_SPEC
        run["continuation"] = record_
    log(s, "HUMAN", f"{gate['id']}: {decision}")
    log(s, "G2_TRANSITION", {"decision": decision, "from": G2_RESULT, "to": to, "round": record_["round"],
                             **({"final": s["final"]["basis"]} if to == COMPLETE else {})})
    s["open_gate"], s["stage"] = None, to


def archive_round(s, decision):
    """Keep the superseded round (SPEC, G1, CHECK_RESULT, memo, critic) before the RUN continues."""
    run = s["run"]
    check, memo = current(run)
    run["rounds"].append({"round": run["round"], "spec": run["spec"], "g1": run["g1"],
                          "check_result": check or None, "memo": memo or None,
                          "pre_critic_check_result_version": (run["check_result"] or {}).get("version"),
                          "critic": run["critic"], "critic_skipped": run["critic_skipped"], "g2_decision": decision})
    run["round"] += 1


def semantics(s) -> dict:
    return s.setdefault("requirement_semantics", {"approved": [], "rejected": []})


def human_approvals(s) -> list:
    """Explicit human approvals of requirement semantics: earlier G1 APPROVEs and the approved design handoff."""
    return [{"signature": a["signature"], "ref": a["ref"]} for a in semantics(s)["approved"]] + \
        G1.handoff_approvals(s.get("approved_handoff"))


def _g1_approve(s, gate, ans):
    """APPROVE_SPEC at G1: every PROPOSED_ENGINEERING_CONSTRAINT explicitly APPROVE or REJECT, every UNKNOWN
    acknowledged. A rejection sends the SPEC back to the RUN for a redraft; nothing reaches research."""
    run = s["run"]
    rows = run.get("g1_rows")
    if rows is None:
        rows = run["g1_rows"] = G1.classify_spec(run["spec"], effective_statement(s), human_approvals(s))
    decisions, problems = G1.decide(rows, ans)
    if problems:
        raise Refused("G1 approval is not explicit for every requirement (silence is not approval): " + "; ".join(problems))
    ref = f"{gate['id']}-APPROVE_SPEC"
    sem = semantics(s)
    for r in rows:
        entry = {"signature": r["signature"], "ref": ref, "id": r["id"], "text": r["text"]}
        if r["semantic"] == G1.PROPOSED and decisions[r["id"]] == "APPROVE":
            sem["approved"].append(entry)
        elif decisions.get(r["id"]) == "REJECT":
            sem["rejected"].append(entry)
    rejected = [r for r in rows if decisions.get(r["id"]) == "REJECT"]
    if rejected:
        log(s, "G1_SEMANTICS", "rejected: " + ", ".join(r["id"] for r in rejected))
        run["g1_rows"] = None
        s["open_gate"], s["stage"] = None, RUN_SPEC
        return
    run["g1"] = {"gate": gate["id"], "ref": ref,
                 "rows": [{**{k: r[k] for k in ("id", "class", "semantic", "text", "signature")},
                           "decision": decisions[r["id"]]} for r in rows]}
    run["g1_approved"] = True
    s["open_gate"], s["stage"] = None, RUN_RESEARCH


def _design_answer(s, gate, decision, ans):
    caps = s["capabilities"]
    if decision == "SUPPLY_INFORMATION":
        if not str(ans.get("text", "")).strip():
            raise Refused("SUPPLY_INFORMATION needs the information as text")
        s["clarifications"].append({"gate": gate["id"], "text": ans["text"].strip()})
        s["out_of_scope"] = out_of_scope_items(effective_statement(s))
        s["field_design"] = s["handoff"] = None
        s["open_gate"], s["stage"] = None, FIELD_DESIGN
    elif decision == "APPROVE_DISCOVERY":
        tags = ans.get("tags") or []
        searchable = {g["tag"] for g in caps["gaps"] if caps["decisions"].get(g["tag"], {}).get("decision") == "SEARCH_REQUIRED"}
        if not tags or not set(tags) <= searchable:
            raise Refused(f"discovery can be approved only for gaps the resolver could not cover {sorted(searchable)}")
        caps["approved_discovery"] = sorted(set(caps["approved_discovery"]) | set(tags))
        for t in tags:
            caps["decisions"].pop(t, None)
        s["open_gate"], s["stage"] = None, CAPABILITY_DISCOVERY
    elif decision == "APPROVE_HANDOFF":
        ack = ans.get("acknowledged_unknowns") or []
        accepted = s["blockers"] if ack == "ALL" or ack == ["ALL"] else ack
        missing = [b for b in s["blockers"] if fde_check.norm(b) not in {fde_check.norm(a) for a in accepted}]
        if missing:
            raise Refused("approving the handoff would rest the selection on unknowns you have not accepted: "
                          + "; ".join(missing) + ". Acknowledge them (or 'ALL'), or SUPPLY_INFORMATION")
        human_caps = ans.get("capabilities") or {}
        undecided = [g["tag"] for g in caps["gaps"] if human_caps.get(g["tag"]) not in ("APPROVED", "DEFERRED")]
        if undecided:
            raise Refused("capability gaps need your decision (APPROVED or DEFERRED): " + ", ".join(undecided))
        caps["human"] = {t: human_caps[t] for t in (g["tag"] for g in caps["gaps"])}
        approved = copy.deepcopy(s["handoff"])
        approved["status"] = "APPROVED"
        approved["approval_ref"] = f"{gate['id']}-APPROVE_HANDOFF"
        s["approved_handoff"], s["acknowledged_unknowns"] = approved, list(accepted)
        s["open_gate"], s["stage"] = None, RUN_SPEC
    else:
        raise Refused("the design gate takes APPROVE_HANDOFF, SUPPLY_INFORMATION, APPROVE_DISCOVERY or STOP")


# ---------------------------------------------------------------- rendering

def run_request(state) -> str:
    """The request handed to the engineering-research RUN skill."""
    if state["route"] == "SELECTION_LED":
        text = effective_statement(state)
    elif state["approved_handoff"]:
        text = fde_check.render_handoff(state["approved_handoff"]).rstrip()
        if state["acknowledged_unknowns"]:
            text += "\n\nUnknowns I accept for this selection (keep them UNKNOWN; do not assume values):\n" + \
                    "\n".join(f"- {u}" for u in state["acknowledged_unknowns"])
    else:
        raise Refused(f"no RUN request yet: {state['route'] or 'unrouted'} problem at stage {state['stage']}")
    for item in state["out_of_scope"]:
        text += f"\n\nOut of scope (stated by the user): {item['quote']}"
    sem = state.get("requirement_semantics") or {}
    if sem.get("rejected"):
        text += ("\n\nAt G1 I rejected these proposed engineering constraints as HARD requirements; redraft the "
                 "SPEC without them as HARD (my stated values stay as I stated them):\n"
                 + "\n".join(f"- {r['id']}: {r['text']}" for r in sem["rejected"]))
    if sem.get("approved"):
        text += ("\n\nAt G1 I explicitly approved these engineering constraints:\n"
                 + "\n".join(f"- {r['id']}: {r['text']}" for r in sem["approved"]))
    cont = (state["run"].get("continuation") if state["stage"] in (RUN_SPEC, RUN_RESEARCH, RUN_CRITIC_HANDOFF) else None)
    if cont:
        prev = state["run"]["rounds"][-1] if state["run"].get("rounds") else {}
        version = (prev.get("check_result") or {}).get("version")
        text += f"\n\nAt G2 (round {cont['round']}) I decided {cont['decision']}"
        text += (f" for {', '.join(cont['candidates'])}" if cont.get("candidates") else "") + (f": {cont['text']}" if cont["text"] else ".")
        text += {"ADDITIONAL_RESEARCH": f"\nContinue the RUN from the latest artifacts (SPEC as approved at G1, CHECK_RESULT_v{version}); "
                                        "keep the evidence already gathered, research what I named, re-evaluate the candidates and "
                                        f"write CHECK_RESULT_v{(version or 0) + 1}. Then stop at CRITIC HANDOFF if there is a leader, "
                                        "otherwise at G2.",
                 "VERIFY_DIFFERENT_CANDIDATE": f"\nContinue the RUN from the latest artifacts (SPEC as approved at G1, CHECK_RESULT_v{version}); "
                                               "verify the candidate(s) I named against the frozen SPEC and write "
                                               f"CHECK_RESULT_v{(version or 0) + 1}. Then stop at CRITIC HANDOFF if there is a leader, "
                                               "otherwise at G2.",
                 "REOPEN_SPEC": "\nReopen the SPEC with this change, redraft it and stop at G1 for my explicit approval; "
                                "no research until I approve it. Keep the earlier evidence for re-use after approval.",
                 "ADVANCE_TO_VERIFICATION": f"\nThe leader {state['run'].get('advance_target')} has no critic PASS yet: write the "
                                            "CRITIC_BRIEF for the latest CHECK_RESULT and stop at CRITIC HANDOFF; no new research."
                 }[cont["decision"]]
        still = [f for f in state.get("critic_findings") or [] if f.get("status") in (M.MATERIAL, M.INSUFFICIENT)]
        if still and cont["decision"] != "ADVANCE_TO_VERIFICATION":
            text += ("\nOpen critic findings (materiality gate) the RUN must address; record the SOFT values you find in "
                     "memo.soft_values:\n" + "\n".join(f"- {finding_line(f)}" for f in still))
    return text.strip() + "\n"


def completed_stages(state) -> list[str]:
    names = {"PROBLEM_ROUTE": "Problem Router", "FIELD_DESIGN": "Field/Design Expert",
             "CAPABILITY_DECISION": "Capability Resolver", "CRITIC_RESULT": "Critic"}
    out = []
    for h in state["history"]:
        name = names.get(h["event"]) or ("Engineering Research RUN" if h["event"] == "RUN_STOP" else None)
        if name and name not in out:
            out.append(name)
    return out


def next_from_user(state) -> str:
    g = state["open_gate"]
    st = state["stage"]
    if g:
        if st == CLARIFY_GATE:
            return "Answer: " + " | ".join(g["questions"])
        if st == DESIGN_GATE:
            if g["blockers"]:
                return ("Supply or decide: " + "; ".join(g["blockers"])
                        + " - or approve the handoff and accept them as UNKNOWN")
            return "Approve the design handoff (or change it) so selection can start"
        if st == G1_GATE:
            need = g.get("decisions_needed") or []
            unk = g.get("unknowns") or []
            return ("Approve or change the draft SPEC (G1)"
                    + (f"; APPROVE or REJECT each proposed engineering constraint ({', '.join(need)})" if need else "")
                    + (f"; acknowledge the UNKNOWN rows ({', '.join(unk)}) or supply them" if unk else ""))
        if st == CRITIC_GATE:
            return "Run engineering-research-critic in a fresh session on the CRITIC_BRIEF and bring back the CRITIC_RESULT"
        if st == G2_RESULT:
            return ("Decide at G2: " + "; ".join(o.split(" (")[0] for o in g["options"]))
    if st in (COMPLETE, STOPPED):
        return "Nothing - the selection is " + st.lower()
    if st == RUN_CRITIC_HANDOFF:
        return f"Nothing yet - the RUN writes the CRITIC_BRIEF for {state['run']['advance_target']}, then you run the critic"
    return f"Nothing yet - next the system runs {STAGE_SKILL.get(st, st)}"


def status(state) -> dict:
    route = state["route_artifact"] or {}
    known = [c["item"] for c in route.get("fixed_constraints", [])]
    h = state["approved_handoff"] or state["handoff"] or {}
    known += [f"{v['parameter']}: {v['value']} {v.get('unit', '')} ({', '.join(v.get('qualifiers', []))}, reference only)".replace("  ", " ")
              for v in h.get("reference_values", [])]
    known += [f"{r['parameter']} {r['operator']} {r['value']} {r.get('unit', '')}".strip() for r in h.get("hard_requirements", [])]
    blocking = list(state["blockers"]) if state["stage"] in (DESIGN_GATE, FIELD_DESIGN, CAPABILITY_RESOLUTION) else []
    if state["stage"] == CLARIFY_GATE:
        blocking = list(state["open_gate"]["questions"])
    if state["stage"] == G1_GATE:
        rows = {r["id"]: r for r in state["open_gate"].get("requirements", [])}
        blocking = [f"{i} proposed engineering constraint, needs your APPROVE or REJECT: {rows[i]['text']}"
                    for i in state["open_gate"].get("decisions_needed", [])]
        blocking += [f"{i} UNKNOWN (stays UNKNOWN unless you supply it): {rows[i]['text']}"
                     for i in state["open_gate"].get("unknowns", [])]
    blocking += [f"capability gap: {g['tag']}" for g in state["capabilities"]["gaps"]
                 if state["capabilities"]["human"].get(g["tag"]) is None and state["approved_handoff"] is None]
    return {"artifact": "ENGINEERING_SELECTION_STATUS",
            "problem_type": state["route"] or "NOT_ROUTED",
            "meaning": ROUTE_MEANING.get(state["route"], "not routed yet"),
            "objective": route.get("stated_objective", ""),
            "known": known, "blocking_selection": blocking,
            "out_of_scope": [i["quote"] for i in state["out_of_scope"]],
            "stage": state["stage"], "skill": STAGE_SKILL.get(state["stage"], "HUMAN" if state["open_gate"] else None),
            "completed": completed_stages(state),
            "open_gate": (state["open_gate"] or {}).get("id"),
            "recommendation": (state["open_gate"] or {}).get("recommendation"),
            "needs_from_user": next_from_user(state)}


def render_status(state) -> str:
    st = status(state)
    lines = ["ENGINEERING_SELECTION_STATUS",
             f"- problem type: {st['problem_type']} ({st['meaning']})"]
    if st["objective"]:
        lines.append(f"- objective: {st['objective']}")
    lines.append("- known: " + ("; ".join(st["known"]) if st["known"] else "nothing confirmed yet"))
    if st["out_of_scope"]:
        lines.append("- out of scope (yours): " + "; ".join(st["out_of_scope"]))
    lines.append("- blocking selection: " + ("; ".join(st["blocking_selection"]) if st["blocking_selection"] else "nothing"))
    lines.append(f"- stage: {st['stage']}" + (f" (gate {st['open_gate']}, waiting for you)" if st["open_gate"] else "")
                 + (f" - done: {', '.join(st['completed'])}" if st["completed"] else ""))
    if st["recommendation"]:
        lines.append(f"- recommendation: {st['recommendation']}")
    lines.append(f"- needed from you: {st['needs_from_user']}")
    return "\n".join(lines) + "\n"


def confidence(state) -> tuple[str, str]:
    run = state["run"]
    critic = run["critic"]
    if run["critic_skipped"]:
        return "LOW", "critic skipped by the human; the leader was not independently attacked"
    if critic is None:
        if (run["memo"] or {}).get("preferred") is not None:
            return "NONE", "critic pending"
        lanes = [c.get("lane") for c in (run["check_result"] or {}).get("candidates", [])]
        if "SPECIFY NOW" not in lanes:
            return "LOW", "no candidate is technically qualified (no SPECIFY NOW), so there is no leader for a critic to attack"
        return "MEDIUM", "no preferred candidate, so no critic pass"
    if critic["label"] == 3 and critic_clear(state):
        return ("MEDIUM", f"leader survived the critic's HARD attack; label 3 findings all NON_MATERIAL or resolved "
                f"({critic['basis']}; independence {critic['independence_quality']})")
    if critic["label"] != 4:
        return "LOW", f"critic label {critic['label']} changed the result; the RUN re-checked it once"
    if critic["basis"].startswith("advisory") or critic["independence_quality"] != "STRONG":
        return "MEDIUM", f"leader survived the critic ({critic['basis']}; independence {critic['independence_quality']})"
    return "HIGH", "leader survived an independent critic (er-core computed label 4, STRONG independence)"


def result(state) -> dict:
    if state["stage"] not in (G2_RESULT, COMPLETE):
        raise Refused(f"no ENGINEERING_SELECTION_RESULT at stage {state['stage']}: the selection is not at G2")
    state = upgrade(copy.deepcopy(state))
    run = state["run"]
    check, memo = current(run)
    cands = {c["candidate_id"]: c for c in check.get("candidates", [])}
    final = state["final"] if state["stage"] == COMPLETE else None
    withheld = bool(final) and final["basis"] == "HUMAN_STOP_NO_RECOMMENDATION"
    order = [] if withheld else ([memo["preferred"]] if memo.get("preferred") else []) + \
        [c for c in cands if c != memo.get("preferred") and cands[c]["lane"] == "SPECIFY NOW"]
    recommended = [{"candidate_id": c, "name": cands[c].get("name", c), "lane": cands[c]["lane"],
                    "hard": {rid: cell["status"] for rid, cell in cands[c]["cells"].items()}} for c in order]
    spec = run["spec"] or {}
    g1_rows = {r["id"]: r for r in (run.get("g1") or {}).get("rows", [])}
    level, why = confidence(state)
    critic = run["critic"]
    critic_line = ("SKIPPED by the human" if run["critic_skipped"] else
                   "not run (no preferred candidate)" if critic is None else
                   f"label {critic['label']}: {critic['text']} ({critic['basis']}"
                   + (f"; critic changed the result, applied in CHECK_RESULT_v{check.get('version')}" if critic["label"] != 4 else "")
                   + (f"; pass {critic.get('pass')}" if critic.get("pass") else "")
                   + ")")
    if final is None:
        selection_status = "PROVISIONAL: waiting for the G2 decision (final only after a critic PASS or an explicit stop)"
    elif withheld:
        selection_status = (f"FINAL, NO RECOMMENDATION: the human ended the selection at G2 ({final['decision']})"
                            + (f"; critic-passed leader {final['critic_pass_withheld']} not recommended"
                               if final.get("critic_pass_withheld") else ""))
    elif final["basis"] == "CRITIC_PASS":
        selection_status = (f"FINAL: {final['preferred']} passed the independent critic (label {final['critic_label']}) "
                            f"on CHECK_RESULT_v{final['check_result_version']}; advanced to verification at G2")
    else:
        selection_status = (f"FINAL: {final['preferred']} survived the independent critic's HARD attack (label "
                            f"{final['critic_label']}, pass {final['critic_pass_no']}); every critic finding is resolved or "
                            f"NON_MATERIAL on CHECK_RESULT_v{final['check_result_version']}; advanced to verification at G2")
    return {"artifact": "ENGINEERING_SELECTION_RESULT", "problem_type": state["route"],
            "selection_status": selection_status, "terminal": final is not None,
            "terminal_basis": (final or {}).get("basis"), "rounds": run["round"],
            "recommended": recommended,
            "requirements": [{"id": r["id"], "class": G1.row_class(r), "requirement": f"{r['parameter']} {r['operator']} {r['value']} {r.get('unit', '')}".strip(),
                              **({"g1": g1_rows[r["id"]]["semantic"], "g1_decision": g1_rows[r["id"]]["decision"]}
                                 if r["id"] in g1_rows else {})}
                             for r in spec.get("requirements", [])],
            "evidence_summary": {c: {"lane": cands[c]["lane"],
                                     "pass": sum(1 for x in cands[c]["cells"].values() if x["status"] == "PASS"),
                                     "not_pass": sorted(r for r, x in cands[c]["cells"].items() if x["status"] != "PASS")}
                                 for c in cands},
            "tradeoffs": memo.get("tradeoffs", []),
            "unresolved_risks": memo.get("unresolved_risks", []) + [f"accepted unknown: {u}" for u in state["acknowledged_unknowns"]]
                                + [f"critic {'caveat' if c['disposition'] == 'CLOSED_BY_CRITIC' else 'limitation'} {c['id']} "
                                   f"({c['concern_type']}, {c['disposition']}): {c['summary']}"
                                   for c in state.get("critic_caveats") or []],
            "critic": critic_line, "confidence": level, "confidence_basis": why,
            "next_engineering_action": memo.get("next_action", "G2 human decision"),
            "critic_findings": [{"id": f["id"], "critic_pass": f["critic_pass"], "kind": f["kind"],
                                 "candidate": f.get("candidate_id") or f.get("candidate_name") or f.get("candidate"),
                                 "summary": f["summary"], "materiality": f.get("class"), "status": f.get("status"),
                                 "reasons": f.get("reasons")} for f in state["critic_findings"]],
            "open_critic_findings": [f["id"] for f in open_findings(state)],
            "human_decision": state["g2_decision"], "g2_decisions": state["g2_decisions"]}


def render_result(state) -> str:
    r = result(state)
    lines = ["ENGINEERING_SELECTION_RESULT", f"- problem type: {r['problem_type']}", f"- status: {r['selection_status']}",
             "- recommended:"]
    none = ("  - none: no recommendation (ended by the human at G2)" if r["terminal_basis"] == "HUMAN_STOP_NO_RECOMMENDATION"
            else "  - none qualifies (see evidence summary)")
    lines += [f"  - {c['name']} [{c['lane']}]" for c in r["recommended"]] or [none]
    lines.append("- requirements: " + "; ".join(f"{q['id']} ({q['class']}"
                                                + (f", {q['g1']}" if q.get("g1") else "") + f") {q['requirement']}"
                                                for q in r["requirements"]))
    lines.append("- evidence summary: " + "; ".join(f"{c}: {v['lane']}, {v['pass']} HARD PASS"
                                                  + (f", open {', '.join(v['not_pass'])}" if v["not_pass"] else "")
                                                  for c, v in r["evidence_summary"].items()))
    lines.append("- tradeoffs: " + ("; ".join(r["tradeoffs"]) or "none recorded"))
    lines.append("- unresolved risks: " + ("; ".join(r["unresolved_risks"]) or "none recorded"))
    lines.append(f"- critic: {r['critic']}")
    if r["critic_findings"]:
        lines.append("- critic findings (materiality): " + "; ".join(
            f"{f['id']} {f['kind']} {f['candidate']}: {f['status']}" for f in r["critic_findings"]))
    lines.append(f"- confidence / evidence quality: {r['confidence']} ({r['confidence_basis']})")
    lines.append(f"- next engineering action: {r['next_engineering_action']}")
    if r["g2_decisions"]:
        lines.append("- G2 decisions: " + "; ".join(f"round {d['round']} {d['decision']}" for d in r["g2_decisions"]))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- CLI

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=("init", "record", "answer", "status", "result", "request"))
    ap.add_argument("--state", type=Path, required=True)
    ap.add_argument("--statement", type=Path)
    ap.add_argument("--artifact", type=Path)
    ap.add_argument("--answer", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.command == "init":
            if not args.statement:
                ap.error("init needs --statement")
            state = new_state(args.statement.read_text("utf-8"))
        else:
            state = json.loads(args.state.read_text("utf-8"))
            if args.command == "record":
                state = record(state, json.loads(args.artifact.read_text("utf-8")))
            elif args.command == "answer":
                state = answer(state, json.loads(args.answer.read_text("utf-8")))
    except (OSError, ValueError) as exc:
        print(f"INPUT ERROR: {exc}", file=sys.stderr)
        return 2
    except Refused as exc:
        print(f"REFUSED {exc}")
        print(f"(state unchanged; stage {json.loads(args.state.read_text('utf-8'))['stage'] if args.state.exists() else '-'})")
        return 1
    try:
        if args.command in ("init", "record", "answer"):
            args.state.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", "utf-8")
        if args.command == "result":
            print(json.dumps(result(state), indent=2) if args.json else render_result(state), end="" if not args.json else "\n")
        elif args.command == "request":
            print(run_request(state), end="")
        else:
            print(json.dumps(status(state), indent=2) if args.json else render_status(state), end="" if not args.json else "\n")
    except Refused as exc:
        print(f"REFUSED {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
