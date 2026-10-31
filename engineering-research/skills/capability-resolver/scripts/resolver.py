"""Capability Resolver V1: a deterministic CAPABILITY_DECISION from the registry and the evidence.

  python skills/capability-resolver/scripts/resolver.py --request REQUEST.json [--json]
  python skills/capability-resolver/scripts/resolver.py --verify DECISION.json --request REQUEST.json
  python skills/capability-resolver/scripts/resolver.py --list-tags
  python skills/capability-resolver/scripts/resolver.py --validate-registry
  (all take --registry PATH; default capability-registry/registry.json in this repository)

Policy: search what exists -> benchmark -> integrate if useful -> build only the missing gap.
Decisions: USE, INTEGRATE, SEARCH_REQUIRED, BUILD. Matching is exact on capability tags. The
resolver names only registry entries and options given as evidence, and it never installs,
connects or executes anything. Standard-library Python 3.10+, no network.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from adapters import IMPLEMENTED_EXTERNAL_ADAPTERS, LocalRegistryAdapter, PLANNED_ADAPTERS  # noqa: E402

RESOLVER_VERSION = "1.1"
REGISTRY_FORMAT = "1.0"
DEFAULT_REGISTRY = Path(__file__).resolve().parents[3] / "capability-registry" / "registry.json"

DECISIONS = ("USE", "INTEGRATE", "SEARCH_REQUIRED", "BUILD")
TYPES = ("skill", "plugin", "connector", "github_repo", "api", "mcp", "cli", "internal_tool")
STATUSES = ("released", "available", "in_development", "deprecated")
USABLE_STATUSES = ("released", "available")
INSTALL_METHODS = ("plugin", "repo_checkout", "connector", "mcp_config", "api_key", "cli_install",
                   "none")
ENTRY_FIELDS = ("id", "name", "type", "purpose", "status", "source", "install", "capabilities",
                "limitations", "trust", "last_reviewed")
VERDICTS = ("ADEQUATE", "PARTIAL", "INADEQUATE")

TAG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class InputError(ValueError):
    pass


# ---------------------------------------------------------------- registry and request

def validate_registry(registry: dict) -> list[str]:
    problems = []
    if registry.get("registry_format") != REGISTRY_FORMAT:
        problems.append(f"registry_format must be {REGISTRY_FORMAT!r}")
    if not DATE.match(str(registry.get("last_updated", ""))):
        problems.append("last_updated must be YYYY-MM-DD")
    seen = set()
    for i, e in enumerate(registry.get("entries", [])):
        where = f"entries[{i}] ({e.get('id', '?')})"
        missing = [f for f in ENTRY_FIELDS if f not in e]
        extra = sorted(set(e) - set(ENTRY_FIELDS))
        if missing:
            problems.append(f"{where}: missing {', '.join(missing)}")
            continue
        if extra:
            problems.append(f"{where}: unknown field(s) {', '.join(extra)}")
        if not TAG.match(e["id"]):
            problems.append(f"{where}: id must be a kebab-case tag")
        if e["id"] in seen:
            problems.append(f"{where}: duplicate id")
        seen.add(e["id"])
        if e["type"] not in TYPES:
            problems.append(f"{where}: type {e['type']!r} not in {TYPES}")
        if e["status"] not in STATUSES:
            problems.append(f"{where}: status {e['status']!r} not in {STATUSES}")
        if not e["source"].get("location"):
            problems.append(f"{where}: source.location is required")
        if e["install"].get("method") not in INSTALL_METHODS or "instructions" not in e["install"]:
            problems.append(f"{where}: install needs method in {INSTALL_METHODS} and instructions")
        if not e["capabilities"] or not all(TAG.match(t) for t in e["capabilities"]):
            problems.append(f"{where}: capabilities must be a non-empty list of kebab-case tags")
        if not e["trust"] or not e["name"] or not e["purpose"]:
            problems.append(f"{where}: name, purpose and trust must be non-empty")
        if not DATE.match(str(e["last_reviewed"])):
            problems.append(f"{where}: last_reviewed must be YYYY-MM-DD")
    return problems


def load_registry(path: Path = DEFAULT_REGISTRY) -> dict:
    registry = json.loads(Path(path).read_text(encoding="utf-8"))
    problems = validate_registry(registry)
    if problems:
        raise InputError("invalid registry: " + "; ".join(problems))
    return registry


def normalize_request(request: dict, registry: dict) -> dict:
    """Check the request and return it with defaults. Evidence must not name unsourced options."""
    ids = {e["id"] for e in registry["entries"]}
    if not str(request.get("requested_capability", "")).strip():
        raise InputError("requested_capability is required")
    required = list(dict.fromkeys(request.get("required_capabilities") or []))
    if not required or not all(isinstance(t, str) and TAG.match(t) for t in required):
        raise InputError("required_capabilities must be a non-empty list of kebab-case tags")
    available = list(request.get("already_available") or [])
    unknown = [i for i in available if i not in ids]
    if unknown:
        raise InputError(f"already_available names ids not in the registry: {unknown}")
    search = request.get("search_record")
    if search is not None:
        for key in ("sources", "queries"):
            if not search.get(key) or not all(isinstance(s, str) and s for s in search[key]):
                raise InputError(f"search_record.{key} must be a non-empty list of strings")
        if not str(search.get("summary", "")).strip():
            raise InputError("search_record.summary is required")
        external = [s for s in search["sources"] if s in IMPLEMENTED_EXTERNAL_ADAPTERS]
        gate = search.get("review_gate")
        if external:  # GA-01: external discovery becomes evidence only through review_gate.py
            if not isinstance(gate, dict) or not set(external) <= set(gate.get("adapters") or []):
                raise InputError(f"search_record from external discovery {external} did not come "
                                 "through review_gate.py; unreviewed discovery is not search evidence")
            n = gate.get("candidates")
            if (not isinstance(n, int) or gate.get("reviewed") != n
                    or len(request.get("evaluated_options") or []) < n):
                raise InputError("review_gate attestation incomplete: every discovered candidate "
                                 "needs a verdict in evaluated_options")
    evaluated = []
    for o in request.get("evaluated_options") or []:
        oid = o.get("id", "")
        if not TAG.match(str(oid)):
            raise InputError(f"evaluated option id {oid!r} must be a kebab-case tag")
        if o.get("verdict") not in VERDICTS:
            raise InputError(f"evaluated option {oid}: verdict must be one of {VERDICTS}")
        if not str(o.get("reason", "")).strip():
            raise InputError(f"evaluated option {oid}: reason is required")
        if oid not in ids and (search is None or not str(o.get("source", "")).strip()):
            raise InputError(f"evaluated option {oid} is not in the registry: it needs a source "
                             "and a search_record that found it")
        adequate_for = [t for t in (o.get("adequate_for") or []) if t in required]
        if o["verdict"] == "ADEQUATE" and not o.get("adequate_for"):
            adequate_for = list(required)
        evaluated.append({**o, "in_registry": oid in ids, "adequate_for": adequate_for})
    if len({o["id"] for o in evaluated}) != len(evaluated):
        raise InputError("evaluated_options ids must be unique")
    return {"requested_capability": request["requested_capability"].strip(),
            "required_capabilities": required, "already_available": available,
            "search_record": search, "evaluated_options": evaluated}


# ---------------------------------------------------------------- decision

def resolve(request: dict, registry: dict, adapters=None) -> dict:
    req = normalize_request(request, registry)
    required = req["required_capabilities"]
    entries = {e["id"]: e for e in registry["entries"]}
    adapters = adapters if adapters is not None else [LocalRegistryAdapter(registry)]
    external = [a.name for a in adapters if getattr(a, "external", True)]
    if external:
        raise InputError(f"external adapter(s) {external} cannot feed the resolver directly: their "
                         "candidates are UNREVIEWED; review them and pass verdicts as "
                         "evaluated_options with their search_record")
    evaluated = {o["id"]: o for o in req["evaluated_options"]}

    matches = []
    for cand in (c for a in adapters for c in a.search(required)):
        covers = [t for t in required if t in cand["capabilities"]]
        verdict = evaluated.get(cand["id"], {}).get("verdict")
        matches.append({"id": cand["id"], "name": cand["name"], "type": cand["type"],
                        "status": cand["status"], "adapter": cand["adapter"],
                        "usable": cand["status"] in USABLE_STATUSES, "covers": covers,
                        "missing": [t for t in required if t not in covers],
                        "evaluated_verdict": verdict})
    viable = [m for m in matches if m["evaluated_verdict"] != "INADEQUATE"]
    external_viable = [o for o in req["evaluated_options"]
                       if not o["in_registry"] and o["verdict"] != "INADEQUATE"]

    covered = {t for m in viable if m["usable"] for t in m["covers"]}
    covered |= {t for o in req["evaluated_options"] for t in o["adequate_for"]}
    adequate = {t for m in viable if m["usable"] and m["evaluated_verdict"] != "PARTIAL"
                for t in m["covers"]}
    adequate |= {t for o in req["evaluated_options"] for t in o["adequate_for"]}
    external_partial = [o["id"] for o in external_viable if o["verdict"] == "PARTIAL"]
    gaps, coverage = [], {}
    for t in required:
        if t in covered:
            coverage[t] = "ADEQUATE" if t in adequate else "PARTIAL"
            continue
        partial = ([f"{m['id']} ({m['status']}, not usable)" for m in viable if t in m["covers"]]
                   + [f"{i} (evaluated PARTIAL)" for i in external_partial])
        if partial:
            detail = f"partial coverage only: {', '.join(partial)}; no option is adequate for it"
            if external_partial and len(required) > 1:
                detail += (" (PARTIAL verdicts apply to the whole request; resolve this gap in its "
                           "own request for per-gap attribution)")
        else:
            detail = "no coverage: no registry entry or evaluated option covers it"
        coverage[t] = "PARTIAL" if partial else "NONE"
        gaps.append({"capability": t, "coverage": coverage[t], "detail": detail})
    gap_tags = [g["capability"] for g in gaps]

    searched_externally = searched_externally_in(req)
    full = [m for m in viable
            if m["usable"] and not m["missing"] and m["evaluated_verdict"] != "PARTIAL"]

    if full:
        decision, recommended = "USE", [m["id"] for m in full]
        rationale = (f"{', '.join(recommended)} is known, usable and covers every required "
                     "capability; nothing needs to be integrated or built.")
    elif viable or external_viable:
        decision = "INTEGRATE"
        recommended = [m["id"] for m in viable] + [o["id"] for o in external_viable]
        rationale = ("Known or evaluated options cover part of the need "
                     f"({', '.join(recommended)}); extend or combine them rather than build. "
                     + (f"Not adequately covered: {', '.join(gap_tags)}." if gap_tags
                        else "Together they cover every required tag, but no single usable "
                        "option covers it all with an adequate verdict; benchmark the combination."))
    elif (matches or req["evaluated_options"]) and not gaps:
        decision = "INTEGRATE"
        recommended = [o["id"] for o in req["evaluated_options"] if o["adequate_for"]]
        rationale = ("Every option was judged inadequate on its own, but their adequate parts "
                     "together cover every required capability; integrate those parts.")
    elif searched_externally:
        decision = "BUILD"
        recommended = [o["id"] for o in req["evaluated_options"] if o["adequate_for"]]
        rationale = (f"Search recorded ({', '.join(req['search_record']['sources'])}) and every "
                     "known or found option was evaluated INADEQUATE with a reason. Build only "
                     f"the gap: {', '.join(gap_tags)}."
                     + (f" Reuse {', '.join(recommended)} for the parts judged adequate."
                        if recommended else ""))
    else:
        decision, recommended = "SEARCH_REQUIRED", []
        rationale = ("No registry entry or evaluated option covers "
                     f"{', '.join(gap_tags)}"
                     + (", and the known matches were judged inadequate" if matches else "")
                     + ". BUILD needs a recorded external search first; nothing is invented.")

    approval, approval_reason = approval_for(decision, recommended, entries, req)
    return {"CAPABILITY_DECISION": {
        "requested_capability": req["requested_capability"],
        "required_capabilities": required,
        "registry_matches": matches,
        "gaps": gaps,
        "coverage": coverage,
        "decision": decision,
        "recommended": recommended,
        "rationale": rationale,
        "next_action": next_action(decision, recommended, gap_tags, entries, req),
        "human_approval_required": approval,
        "approval_reason": approval_reason,
        "resolver": {"version": RESOLVER_VERSION, "registry_format": registry["registry_format"],
                     "adapters_used": [a.name for a in adapters]},
    }}


def searched_externally_in(req):
    return bool(req["search_record"]) and any(
        s != "local_registry" for s in req["search_record"]["sources"])


def search_hint():
    return (f"available adapters: {', '.join(IMPLEMENTED_EXTERNAL_ADAPTERS)} "
            "(skills/capability-resolver/scripts/; results UNREVIEWED until passed through "
            f"review_gate.py); planned: {', '.join(PLANNED_ADAPTERS)}; otherwise a recorded "
            "manual search")


def approval_for(decision, recommended, entries, req):
    if decision == "SEARCH_REQUIRED":
        return "NO", ("Searching is read-only. Anything it finds comes back through the resolver "
                      "before it can be adopted.")
    if decision == "USE":
        to_install = [i for i in recommended if i not in req["already_available"]
                      and entries[i]["install"]["method"] != "none"]
        if not to_install:
            return "NO", "Already available in this environment; nothing to install or connect."
        return "YES", (f"Installing or connecting {', '.join(to_install)} "
                       f"({', '.join(entries[i]['install']['method'] for i in to_install)}) "
                       "needs human approval; the resolver does not do it.")
    if decision == "INTEGRATE":
        return "YES", "Integrating, extending or connecting a capability changes the toolset."
    return "YES", "BUILD starts new development; a human approves the build scope first."


def next_action(decision, recommended, gap_tags, entries, req):
    if decision == "USE":
        steps = [f"{i}: already available, use it" if i in req["already_available"]
                 else f"{i}: after approval, {entries[i]['install']['instructions']}"
                 for i in recommended]
        return "Use the known capability. " + " | ".join(steps)
    if decision == "INTEGRATE":
        text = f"Benchmark {', '.join(recommended)} against the request."
        if gap_tags and searched_externally_in(req):
            text += (f" The search is already recorded ({', '.join(req['search_record']['sources'])}"
                     f"); do not repeat it. Benchmark the options against {', '.join(gap_tags)}, "
                     "then extend or combine them; build only what the benchmark shows stays "
                     "uncovered (BUILD needs those options re-evaluated INADEQUATE with a reason).")
        elif gap_tags:
            text += (f" Search existing options for {', '.join(gap_tags)} before any build "
                     f"({search_hint()}). Then extend or combine; build only what stays uncovered.")
        unregistered = [i for i in recommended if i not in entries]
        if unregistered:
            text += (f" Add {', '.join(unregistered)} to the capability registry after review "
                     "before relying on it.")
        return text
    if decision == "BUILD":
        return (f"Write a build proposal limited to {', '.join(gap_tags)} for human approval. "
                "Register the new capability in the registry once it is built and tested.")
    return (f"Search existing options for {', '.join(req['required_capabilities'])} "
            f"({search_hint()}). "
            "Record search_record (sources, queries, summary) and an evaluated_options verdict "
            "(ADEQUATE / PARTIAL / INADEQUATE, with reason) for each candidate, then re-run the "
            "resolver.")


def verify_decision(decision: dict, request: dict, registry: dict) -> list[str]:
    """Check a CAPABILITY_DECISION (e.g. written by a model) against a recomputed one."""
    got = decision.get("CAPABILITY_DECISION", decision)
    want = resolve(request, registry)["CAPABILITY_DECISION"]
    known = ({e["id"] for e in registry["entries"]}
             | {o.get("id") for o in request.get("evaluated_options") or []})
    problems = []
    if got.get("decision") not in DECISIONS:
        problems.append(f"decision {got.get('decision')!r} is not one of {DECISIONS}")
    for m in got.get("registry_matches", []):
        mid = m.get("id") if isinstance(m, dict) else m
        if mid not in {e["id"] for e in registry["entries"]}:
            problems.append(f"registry match {mid!r} is not in the registry (invented)")
    for rid in got.get("recommended", []):
        if rid not in known:
            problems.append(f"recommended {rid!r} is in neither the registry nor the evidence "
                            "(invented)")
    for key in ("decision", "recommended", "human_approval_required"):
        if got.get(key) != want[key]:
            problems.append(f"{key}: {got.get(key)!r}, resolver computes {want[key]!r}")
    got_ids = sorted(m.get("id") if isinstance(m, dict) else m
                     for m in got.get("registry_matches", []))
    if got_ids != sorted(m["id"] for m in want["registry_matches"]):
        problems.append(f"registry_matches {got_ids}, resolver computes "
                        f"{sorted(m['id'] for m in want['registry_matches'])}")
    got_gaps = sorted(g.get("capability") if isinstance(g, dict) else g
                      for g in got.get("gaps", []))
    if got_gaps != sorted(g["capability"] for g in want["gaps"]):
        problems.append(f"gaps {got_gaps}, resolver computes "
                        f"{sorted(g['capability'] for g in want['gaps'])}")
    return problems


# ---------------------------------------------------------------- CLI

def render(decision: dict) -> str:
    d = decision["CAPABILITY_DECISION"]
    lines = ["CAPABILITY_DECISION",
             f"- requested capability: {d['requested_capability']}",
             f"- required capabilities: {', '.join(d['required_capabilities'])}",
             "- registry matches:" + ("" if d["registry_matches"] else " none")]
    for m in d["registry_matches"]:
        lines.append(f"  - {m['id']} ({m['type']}, {m['status']}): covers "
                     f"{', '.join(m['covers'])}; missing {', '.join(m['missing']) or 'nothing'}"
                     + (f"; evaluated {m['evaluated_verdict']}" if m["evaluated_verdict"] else ""))
    lines.append("- coverage: " + ", ".join(f"{t} {c}" for t, c in d["coverage"].items()))
    lines.append("- gaps:" + ("" if d["gaps"] else " none"))
    lines += [f"  - {g['capability']} [{g['coverage']}]: {g['detail']}" for g in d["gaps"]]
    lines += [f"- decision: {d['decision']}",
              f"- recommended: {', '.join(d['recommended']) or 'none'}",
              f"- rationale: {d['rationale']}",
              f"- next search/build action: {d['next_action']}",
              f"- human approval required: {d['human_approval_required']} "
              f"({d['approval_reason']})"]
    return "\n".join(lines)


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    ap.add_argument("--request", type=Path)
    ap.add_argument("--verify", type=Path, metavar="DECISION")
    ap.add_argument("--list-tags", action="store_true")
    ap.add_argument("--validate-registry", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        registry = load_registry(args.registry)
        if args.validate_registry:
            print(f"REGISTRY: PASS ({len(registry['entries'])} entries)")
            return 0
        if args.list_tags:
            for e in registry["entries"]:
                print(f"{e['id']} [{e['status']}]: {', '.join(e['capabilities'])}")
            return 0
        if not args.request:
            ap.error("--request is required")
        request = json.loads(args.request.read_text(encoding="utf-8"))
        if args.verify:
            problems = verify_decision(json.loads(args.verify.read_text(encoding="utf-8")),
                                       request, registry)
            for p in problems:
                print(f"PROBLEM {p}")
            print(f"DECISION VERIFY: {'FAIL' if problems else 'PASS'}")
            return 1 if problems else 0
        decision = resolve(request, registry)
    except InputError as exc:
        print(f"INPUT ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(decision, indent=2) if args.json else render(decision))
    return 0


if __name__ == "__main__":
    sys.exit(main())
