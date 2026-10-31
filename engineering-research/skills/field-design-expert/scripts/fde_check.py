"""Field/Design Expert V1 deterministic layer.

  python skills/field-design-expert/scripts/fde_check.py --result RESULT.json --statement STATEMENT.txt
  python skills/field-design-expert/scripts/fde_check.py --handoff HANDOFF.json --statement STATEMENT.txt [--render]
  python skills/field-design-expert/scripts/fde_check.py --result RESULT.json --statement STATEMENT.txt --resolver-requests OUT_DIR

Checks a FIELD_DESIGN_RESULT and an ENGINEERING_RESEARCH_HANDOFF (format 1.1) against the problem
statement:
- every value presented as given (fixed constraint, ready requirement, HARD requirement, reference
  value, known first-order value) carries a verbatim quote from the statement that contains the
  value, so no requirement can be invented; everything else stays UNKNOWN;
- O-P4-01 requirement semantics: a user-supplied number keeps its qualifiers (APPROXIMATE,
  NOMINAL, OBSERVED, SCREENING; STATED when plain), detected from the statement sentence that
  contains it, so trimming the quote cannot drop them. A number becomes a HARD predicate only if
  the user stated the operator right next to the value ("at least 25 kA"; operator_basis
  USER_STATED) or a recorded human approval establishes it (operator_basis HUMAN_APPROVED with an
  approval_ref found in --approvals). Otherwise it stays a reference value (no operator) or an
  UNKNOWN requirement;
- fixed constraints and assumptions to challenge do not overlap;
- several architecture options are never resolved automatically (the choice stays with the human);
- the human gate is YES, and a handoff is a DRAFT until a human approves it;
- no URLs and no names from a heuristic list of commercial vendors (the expert is not product
  discovery).
--render turns a handoff into a plain request for the existing engineering-research RUN skill,
which is unchanged. --resolver-requests writes one Capability Resolver request per declared
capability need, and nothing when there is none (the resolver is not mandatory).

Standard-library Python 3.10+, no network. Exit 0 PASS, 1 FAIL, 2 bad input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

UNKNOWN = "UNKNOWN"
ROUTES = ("SELECTION_LED", "DESIGN_LED", "HYBRID", "INSUFFICIENT_INPUT")
CHOICES = ("ACCEPTED_AS_GIVEN", "OPEN_FOR_HUMAN_DECISION")
RESULT_FIELDS = ("artifact", "problem_route", "system_objective", "current_architecture",
                 "fixed_constraints", "assumptions_to_challenge", "first_order_variables",
                 "architecture_options", "architecture_choice", "required_calculations",
                 "material_compatibility_questions", "controls_operability_questions",
                 "safety_reliability_questions", "requirements_ready_for_selection",
                 "unresolved_requirements", "capability_needs", "recommended_next_step",
                 "human_gate_required")
HANDOFF_FIELDS = ("artifact", "status", "selection_objective", "component_category",
                  "approved_architecture_context", "hard_requirements", "soft_preferences",
                  "unknown_requirements", "required_evidence_types", "known_constraints",
                  "excluded_assumptions", "approved_search_scope", "data_tier", "reference_values")
HARD_FIELDS = ("id", "parameter", "operator", "value", "unit", "condition", "safety_critical",
               "origin", "basis")
FORMAT = "1.1"  # 1.1: requirement semantics preserved (O-P4-01)
QUALIFIERS = ("STATED", "APPROXIMATE", "NOMINAL", "OBSERVED", "SCREENING")
QUALIFIER_WORDS = {
    "APPROXIMATE": r"approximately|approx|about|around|roughly|circa|some",
    "NOMINAL": r"nominal|nominally|rated",
    "OBSERVED": r"current|currently|measured|observed|existing|present|presently",
    "SCREENING": r"screening|considered|provisional|tentative|future|possible|candidate|preliminary",
}
OPERATORS = {">=": (">=", "\u2265", "min", "minimum", "at least"),
             "<=": ("<=", "\u2264", "max", "maximum", "at most", "up to"),
             ">": (">", "greater than", "above"), "<": ("<", "less than", "below"),
             "=": ("=", "==", "equals", "exactly"),
             "range": ("range", "within", "between", "in range", "in")}
OPERATOR_WORDS = {
    ">=": r"at least|minimum|min|no less than|not less than|>=|or more|or greater|or higher",
    "<=": r"at most|maximum|max|no more than|not more than|up to|<=|or less|or lower|not exceed|not to exceed",
    ">": r"greater than|more than|above|exceeding|>",
    "<": r"less than|below|under|<",
    "=": r"exactly|equal to|equals|=",
    "range": r"between|within|range|from",
}
CATEGORICAL_OPERATORS = ("=", "is", "includes", "in")
HANDOFF_STATUSES = ("DRAFT_PENDING_HUMAN_GATE", "APPROVED")
TAG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
URL = re.compile(r"https?://|www\.", re.I)
# Heuristic only: commercial vendor names that must not appear in design-stage output.
VENDORS = ("grundfos", "ksb", "xylem", "lowara", "goulds", "wilo", "ebara", "iwaki", "magnatex",
           "flowserve", "sulzer", "pentair", "speck pumpen", "verder", "tuthill", "liquiflo",
           "micropump", "gorman-rupp", "hydra-cell", "wanner", "prominent", "lewa", "milton roy",
           "pulsafeeder", "siemens", "schneider electric", "eaton", "allen-bradley", "rockwell",
           "omron", "sew-eurodrive", "baldor", "danfoss", "swagelok", "alfa laval", "swep",
           "kelvion", "purolite", "dowex", "energyflowx", "march pump", "cole-parmer", "watson-marlow",
           "masterflex", "leeson", "abb ", "dab pumps", "pedrollo", "calpeda", "salmson", "armstrong fluid")


def norm(text, keep_ops=False) -> str:
    text = str(text).lower().replace("\u2265", " >= ").replace("\u2264", " <= ")
    for a, b in (("–", "-"), ("—", "-"), ("−", "-"), ("°", " deg "),
                 ("‘", "'"), ("’", "'"), ("“", '"'), ("”", '"'),
                 ("~", " approximately "), ("≈", " approximately ")):
        text = text.replace(a, b)
    return " ".join(re.sub(r"[^\w.\-/%'\"+<>=]" if keep_ops else r"[^\w.\-/%'\"+]", " ", text).split())


def quoted(quote, statement) -> bool:
    return isinstance(quote, str) and bool(quote.strip()) and norm(quote) in norm(statement)


def value_in_quote(value, quote) -> bool:
    return norm(value) in norm(quote)


def numeric(value) -> bool:
    return bool(re.search(r"\d", str(value)))


def detected_qualifiers(quote, statement) -> set:
    """Qualifiers in the statement sentence(s) that contain the quote (conservative: whole sentence)."""
    sentences = [x for x in re.split(r"(?<=[.;!?])\s+|\n+", statement) if x.strip()]
    found = set()
    for sentence in sentences:
        if norm(quote) and norm(quote) in norm(sentence):  # norm() turns ~ and \u2248 into "approximately"
            found |= {q for q, words in QUALIFIER_WORDS.items() if re.search(rf"\b(?:{words})\b", norm(sentence))}
    return found


def canonical_operator(op):
    op = str(op).strip().lower()
    for canon, names in OPERATORS.items():
        if op in names:
            return canon
    return None


def operator_stated(operator, value, quote) -> bool:
    """The user's own operator words sit next to the value (no other number in between)."""
    canon = canonical_operator(operator)
    words = norm(quote, keep_ops=True).split()
    target = norm(value, keep_ops=True).split()
    if not canon or not target:
        return False
    for i in range(len(words) - len(target) + 1):
        if words[i:i + len(target)] != target:
            continue
        before, j = [], i - 1
        while j >= 0 and len(before) < 5 and not numeric(words[j]):
            before.insert(0, words[j]); j -= 1
        after, j = [], i + len(target)
        while j < len(words) and len(after) < 4 and not numeric(words[j]):
            after.append(words[j]); j += 1
        window = " ".join(before + ["<v>"] + after)
        if re.search(rf"(?:^|\s)(?:{OPERATOR_WORDS[canon]})(?:\s|$)", window):
            return True
    return False


def semantics_problems(item, statement, where) -> list[str]:
    """A quoted number keeps every qualifier its statement sentence gives it."""
    if not numeric(item.get("value", item.get("current_value", ""))):
        return []
    declared = item.get("qualifiers")
    if not isinstance(declared, list) or not declared or any(q not in QUALIFIERS for q in declared):
        return [f"{where}: a user-supplied number needs qualifiers from {QUALIFIERS}"]
    missing = sorted(detected_qualifiers(item.get("quote", ""), statement) - set(declared))
    if missing:
        return [f"{where}: qualifier(s) {', '.join(missing)} dropped; the statement gives this value as "
                f"{', '.join(missing).lower()} (O-P4-01)"]
    return []


def predicate_problems(r, statement, approvals, where) -> list[str]:
    """O-P4-01: an operator on a user number must be the user's own, or human-approved."""
    p = semantics_problems(r, statement, where)
    if not numeric(r.get("value", "")):
        if str(r.get("operator", "")).strip().lower() not in CATEGORICAL_OPERATORS:
            p.append(f"{where}: a non-numeric requirement takes one of {CATEGORICAL_OPERATORS}")
        return p
    if canonical_operator(r.get("operator")) is None:
        p.append(f"{where}: unknown operator {r.get('operator')!r}")
        return p
    basis = r.get("operator_basis")
    if basis == "USER_STATED":
        if not operator_stated(r["operator"], r.get("value", ""), r.get("quote", "")):
            p.append(f"{where}: operator {r['operator']!r} is not stated by the user next to the value; "
                     "invented operator (O-P4-01). Keep it as a reference value or UNKNOWN requirement")
    elif basis == "HUMAN_APPROVED":
        if r.get("approval_ref") not in approvals:
            p.append(f"{where}: operator_basis HUMAN_APPROVED needs an approval_ref found in the recorded "
                     "human-gate approvals")
    else:
        p.append(f"{where}: a numeric predicate needs operator_basis USER_STATED or HUMAN_APPROVED")
    return p


def load_approvals(path) -> set:
    record = json.loads(Path(path).read_text("utf-8"))
    return {d["id"] for d in record.get("decisions", []) if isinstance(d, dict) and d.get("id")}


def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v)


def product_problems(obj, where) -> list[str]:
    problems = []
    for s in strings(obj):
        if URL.search(s):
            problems.append(f"{where}: contains a URL ({s[:60]!r}); the design stage does no vendor search")
        for v in VENDORS:
            if re.search(rf"(?<![a-z0-9]){re.escape(v.strip())}(?![a-z0-9])", s.lower()):
                problems.append(f"{where}: names a commercial vendor ({v.strip()!r}); the design stage "
                                "names no products")
    return problems


def _list(obj, key):
    value = obj.get(key)
    return value if isinstance(value, list) else []


def check_result(result: dict, statement: str, approvals=frozenset()) -> list[str]:
    if not isinstance(result, dict):
        return ["FIELD_DESIGN_RESULT is not an object"]
    missing = [k for k in RESULT_FIELDS if k not in result]
    if missing:
        return [f"missing field(s): {', '.join(missing)}"]
    p = []
    if result["artifact"] != "FIELD_DESIGN_RESULT":
        p.append("artifact must be FIELD_DESIGN_RESULT")
    if result.get("version") != FORMAT:
        p.append(f"version must be {FORMAT} (requirement semantics, O-P4-01)")
    route = (result["problem_route"] or {}).get("route") if isinstance(result["problem_route"], dict) else None
    if route not in ROUTES:
        p.append("problem_route.route must be a PROBLEM_ROUTE route")
    if result["human_gate_required"] != "YES":
        p.append("human_gate_required must be YES")
    fixed = _list(result, "fixed_constraints")
    for i, c in enumerate(fixed):
        if not isinstance(c, dict) or not quoted(c.get("quote"), statement):
            p.append(f"fixed_constraints[{i}] needs a verbatim quote from the statement")
    fixed_items = {norm(c.get("item", "")) for c in fixed if isinstance(c, dict)}
    for i, a in enumerate(_list(result, "assumptions_to_challenge")):
        if not isinstance(a, dict) or not str(a.get("assumption", "")).strip():
            p.append(f"assumptions_to_challenge[{i}] needs an assumption")
        elif norm(a["assumption"]) in fixed_items:
            p.append(f"assumptions_to_challenge[{i}] is also listed as a fixed constraint")
    variables = _list(result, "first_order_variables")
    if route in ("DESIGN_LED", "HYBRID") and not variables:
        p.append("first_order_variables must not be empty for a design-led or hybrid problem")
    for i, v in enumerate(variables):
        if not isinstance(v, dict) or not str(v.get("variable", "")).strip():
            p.append(f"first_order_variables[{i}] needs a variable")
            continue
        val = v.get("current_value", UNKNOWN)
        if val != UNKNOWN and not (quoted(v.get("quote"), statement) and value_in_quote(val, v.get("quote"))):
            p.append(f"first_order_variables[{i}] ({v['variable']}): a known current_value needs a "
                     "verbatim quote containing it; otherwise UNKNOWN")
        elif val != UNKNOWN:
            p += semantics_problems({**v, "value": val}, statement, f"first_order_variables[{i}]")
    options = _list(result, "architecture_options")
    if result["architecture_choice"] not in CHOICES:
        p.append(f"architecture_choice must be one of {CHOICES} (the expert never picks an option)")
    elif len(options) >= 2 and result["architecture_choice"] != "OPEN_FOR_HUMAN_DECISION":
        p.append("with several architecture options the choice must stay OPEN_FOR_HUMAN_DECISION")
    for i, o in enumerate(options):
        if isinstance(o, dict) and (o.get("selected") or o.get("chosen") or o.get("recommended") is True):
            p.append(f"architecture_options[{i}] is marked as chosen; the human decides")
    calc_ids = []
    for i, c in enumerate(_list(result, "required_calculations")):
        if not isinstance(c, dict) or not str(c.get("id", "")).strip() or not str(c.get("calculation", "")).strip():
            p.append(f"required_calculations[{i}] needs an id and a calculation")
        else:
            calc_ids.append(c["id"])
    if len(calc_ids) != len(set(calc_ids)):
        p.append("required_calculations ids must be unique")
    for i, r in enumerate(_list(result, "requirements_ready_for_selection")):
        if not isinstance(r, dict) or not quoted(r.get("quote"), statement) \
                or not value_in_quote(r.get("value", ""), r.get("quote", "")):
            p.append(f"requirements_ready_for_selection[{i}]: a ready requirement must be quoted from "
                     "the statement with its value (no invented requirements)")
        else:
            p += predicate_problems(r, statement, approvals, f"requirements_ready_for_selection[{i}]")
    for i, u in enumerate(_list(result, "unresolved_requirements")):
        if not isinstance(u, dict) or not str(u.get("parameter", "")).strip():
            p.append(f"unresolved_requirements[{i}] needs a parameter")
        elif u.get("value", UNKNOWN) != UNKNOWN:
            p.append(f"unresolved_requirements[{i}] must keep value UNKNOWN")
        elif str(u.get("resolved_by", "")).startswith("CALC-") and u["resolved_by"] not in calc_ids:
            p.append(f"unresolved_requirements[{i}] refers to an unknown calculation {u['resolved_by']}")
    for i, c in enumerate(_list(result, "capability_needs")):
        if not isinstance(c, dict) or not TAG.match(str(c.get("tag", ""))):
            p.append(f"capability_needs[{i}] needs a kebab-case capability tag")
    return p + product_problems(result, "FIELD_DESIGN_RESULT")


def check_handoff(handoff: dict, statement: str, approvals=frozenset()) -> list[str]:
    if not isinstance(handoff, dict):
        return ["ENGINEERING_RESEARCH_HANDOFF is not an object"]
    missing = [k for k in HANDOFF_FIELDS if k not in handoff]
    if missing:
        return [f"missing field(s): {', '.join(missing)}"]
    p = []
    if handoff["artifact"] != "ENGINEERING_RESEARCH_HANDOFF":
        p.append("artifact must be ENGINEERING_RESEARCH_HANDOFF")
    if handoff.get("version") != FORMAT:
        p.append(f"version must be {FORMAT} (requirement semantics, O-P4-01)")
    if handoff["status"] not in HANDOFF_STATUSES:
        p.append(f"status must be one of {HANDOFF_STATUSES}")
    if handoff["data_tier"] != "T0":
        p.append("data_tier must be T0 (public/synthetic only)")
    for key in ("selection_objective", "component_category", "approved_architecture_context"):
        if not str(handoff[key]).strip():
            p.append(f"{key} is required")
    ids = []
    for i, r in enumerate(_list(handoff, "hard_requirements")):
        if not isinstance(r, dict) or [k for k in HARD_FIELDS if k not in r]:
            p.append(f"hard_requirements[{i}] needs {', '.join(HARD_FIELDS)}")
            continue
        ids.append(r["id"])
        if r["origin"] != "USER":
            p.append(f"hard_requirements[{i}]: origin must be USER (AI ideas go to the RUN skill's "
                     "AI-PROPOSED list at G1)")
        if r["safety_critical"] not in ("YES", "NO", UNKNOWN):
            p.append(f"hard_requirements[{i}]: safety_critical must be YES, NO or UNKNOWN")
        if r["basis"] == "GIVEN":
            if not (quoted(r.get("quote"), statement) and value_in_quote(r["value"], r["quote"])):
                p.append(f"hard_requirements[{i}] ({r['parameter']}): a GIVEN value needs a verbatim "
                         "quote from the statement that contains it")
            else:
                p += predicate_problems(r, statement, approvals, f"hard_requirements[{i}] ({r['parameter']})")
        elif r["basis"] == "APPROVED_DESIGN_DECISION":
            if handoff["status"] != "APPROVED" or r.get("approval_ref") not in approvals:
                p.append(f"hard_requirements[{i}]: a design-derived value is allowed only in an APPROVED "
                         "handoff with an approval_ref found in the recorded human-gate approvals")
        else:
            p.append(f"hard_requirements[{i}]: basis must be GIVEN or APPROVED_DESIGN_DECISION")
    if len(ids) != len(set(ids)):
        p.append("hard_requirements ids must be unique")
    for i, v in enumerate(_list(handoff, "reference_values")):
        where = f"reference_values[{i}]"
        if not isinstance(v, dict) or not str(v.get("parameter", "")).strip():
            p.append(f"{where} needs a parameter")
            continue
        if "operator" in v:
            p.append(f"{where}: a reference value carries no operator (it is context, not a requirement)")
        if not (quoted(v.get("quote"), statement) and value_in_quote(v.get("value", ""), v.get("quote", ""))):
            p.append(f"{where}: needs a verbatim quote containing the value")
        else:
            p += semantics_problems(v, statement, where)
    for i, s in enumerate(_list(handoff, "soft_preferences")):
        if not isinstance(s, dict) or not quoted(s.get("quote"), statement):
            p.append(f"soft_preferences[{i}] needs a verbatim quote (stated by the user)")
    for i, u in enumerate(_list(handoff, "unknown_requirements")):
        if not isinstance(u, dict) or not str(u.get("parameter", "")).strip():
            p.append(f"unknown_requirements[{i}] needs a parameter")
        elif u.get("value", UNKNOWN) != UNKNOWN:
            p.append(f"unknown_requirements[{i}] must keep value UNKNOWN")
    for i, c in enumerate(_list(handoff, "known_constraints")):
        if not isinstance(c, dict) or not quoted(c.get("quote"), statement):
            p.append(f"known_constraints[{i}] needs a verbatim quote")
    scope = handoff["approved_search_scope"]
    if not isinstance(scope, dict) or not scope.get("in_scope"):
        p.append("approved_search_scope.in_scope must not be empty")
    if not _list(handoff, "required_evidence_types"):
        p.append("required_evidence_types must not be empty")
    return p + product_problems(handoff, "ENGINEERING_RESEARCH_HANDOFF")


def render_handoff(h: dict) -> str:
    """Plain request for the unchanged engineering-research RUN skill (its INTAKE fields)."""
    lines = [f"I need a defensible, evidence-graded shortlist of {h['component_category']}.",
             "", f"Engineering objective: {h['selection_objective']}",
             f"Application context: {h['approved_architecture_context']}"]
    if h["status"] != "APPROVED":
        lines.append("Status: DRAFT from a design review, pending my approval. Treat it as a request; "
                     "draft the SPEC and stop at G1.")
    if h["hard_requirements"]:
        lines += ["", "Known requirements (HARD, stated by me):"]
        lines += [f"- {r['parameter']} {r['operator']} {r['value']} {r['unit']}".rstrip()
                  + (f" ({r['condition']})" if r.get("condition") else "")
                  + (f" [{', '.join(r['qualifiers'])}]" if r.get("qualifiers") and r["qualifiers"] != ["STATED"] else "")
                  + (f" [approved: {r['approval_ref']}]" if r.get("operator_basis") == "HUMAN_APPROVED" else "")
                  + (" [safety-critical]" if r["safety_critical"] == "YES" else "")
                  for r in h["hard_requirements"]]
    if h.get("reference_values"):
        lines += ["", "Reference values (context from me, NOT requirements; do not turn them into limits):"]
        lines += [f"- {v['parameter']}: {v['value']} {v.get('unit', '')}".rstrip()
                  + f" [{', '.join(v.get('qualifiers', []))}]"
                  + (f" ({v['semantics']})" if v.get("semantics") else "") for v in h["reference_values"]]
    if h["soft_preferences"]:
        lines += ["", "Preferences (SOFT):"] + [f"- {s['parameter']}: {s['preference']}" for s in h["soft_preferences"]]
    if h["unknown_requirements"]:
        lines += ["", "Not yet known. Do not assume values; propose them as AI-PROPOSED or ask me at G1:"]
        lines += [f"- {u['parameter']}: UNKNOWN" + (f" ({u['why_unknown']})" if u.get("why_unknown") else "")
                  for u in h["unknown_requirements"]]
    if h["known_constraints"]:
        lines += ["", "Known constraints:"] + [f"- {c['item']}" for c in h["known_constraints"]]
    if h["excluded_assumptions"]:
        lines += ["", "Do not assume:"] + [f"- {a}" for a in h["excluded_assumptions"]]
    lines += ["", "Evidence I need for each candidate:"] + [f"- {e}" for e in h["required_evidence_types"]]
    scope = h["approved_search_scope"]
    lines += ["", "Search scope: " + "; ".join(scope.get("in_scope", []))]
    if scope.get("out_of_scope"):
        lines.append("Out of scope: " + "; ".join(scope["out_of_scope"]))
    lines += ["", "Public/synthetic information only (T0)."]
    return "\n".join(lines) + "\n"


def resolver_requests(result: dict) -> list[dict]:
    """One Capability Resolver request per declared capability need; none when there is none."""
    return [{"requested_capability": f"{result.get('system_objective', '')} - {c.get('why', c['tag'])}".strip(" -"),
             "required_capabilities": [c["tag"]]}
            for c in _list(result, "capability_needs") if isinstance(c, dict) and TAG.match(str(c.get("tag", "")))]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--statement", type=Path, required=True)
    ap.add_argument("--result", type=Path)
    ap.add_argument("--handoff", type=Path)
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--approvals", type=Path, help="human-gate record whose decision ids may be cited as approval_ref")
    ap.add_argument("--resolver-requests", type=Path, metavar="OUT_DIR")
    args = ap.parse_args(argv)
    if not args.result and not args.handoff:
        ap.error("give --result and/or --handoff")
    try:
        statement = args.statement.read_text("utf-8")
        result = json.loads(args.result.read_text("utf-8")) if args.result else None
        handoff = json.loads(args.handoff.read_text("utf-8")) if args.handoff else None
        approvals = load_approvals(args.approvals) if args.approvals else set()
    except (OSError, ValueError) as exc:
        print(f"INPUT ERROR: {exc}", file=sys.stderr)
        return 2
    problems = []
    if result is not None:
        problems += [f"RESULT: {x}" for x in check_result(result, statement, approvals)]
    if handoff is not None:
        problems += [f"HANDOFF: {x}" for x in check_handoff(handoff, statement, approvals)]
    for x in problems:
        print(f"PROBLEM {x}")
    print(f"FIELD/DESIGN CHECK: {'FAIL' if problems else 'PASS'}")
    if not problems and args.render and handoff is not None:
        print("\n--- ENGINEERING RESEARCH REQUEST ---\n" + render_handoff(handoff), end="")
    if not problems and args.resolver_requests and result is not None:
        reqs = resolver_requests(result)
        args.resolver_requests.mkdir(parents=True, exist_ok=True)
        for i, r in enumerate(reqs, 1):
            (args.resolver_requests / f"resolver_request_{i}.json").write_text(json.dumps(r, indent=2) + "\n", "utf-8")
        print(f"capability resolver requests written: {len(reqs)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
