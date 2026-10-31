"""Problem Router V1 deterministic layer: recompute and check a PROBLEM_ROUTE.

  python skills/problem-router/scripts/route_check.py --route ROUTE.json --statement STATEMENT.txt [--json]

The model writes the PROBLEM_ROUTE, including its routing_signals (facts it extracted from the
problem). This script recomputes the route from those signals with the fixed rules below and
reports every inconsistency, in the same way er-core recomputes mechanical consequences. Judgment
(which signals are true) stays with the model and the human; the mapping from signals to route
and next stage is mechanical.

Rules (first match wins):
  1. objective_clear is false, or any missing input blocks routing     -> INSUFFICIENT_INPUT
  2. architecture_state UNRESOLVED, or component function not known    -> DESIGN_LED
  3. architecture_state FIXED and no selection-affecting design decision -> SELECTION_LED
  4. otherwise (PARTIAL, or FIXED with selection-affecting decisions)  -> HYBRID
Missing ordinary product requirements do not block routing; they go to the RUN skill's SPEC/G1.

Standard-library Python 3.10+, no network. Exit 0 PASS, 1 FAIL, 2 bad input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROUTES = ("SELECTION_LED", "DESIGN_LED", "HYBRID", "INSUFFICIENT_INPUT")
NEXT_STAGE = {"SELECTION_LED": "ENGINEERING_RESEARCH_RUN",
              "DESIGN_LED": "FIELD_DESIGN_EXPERT",
              "HYBRID": "FIELD_DESIGN_EXPERT_THEN_ENGINEERING_RESEARCH",
              "INSUFFICIENT_INPUT": "CLARIFY_WITH_HUMAN"}
ARCHITECTURE_STATES = ("FIXED", "PARTIAL", "UNRESOLVED")
REQUIRED = ("artifact", "route", "stated_objective", "routing_signals", "fixed_constraints",
            "uncertain_constraints", "architecture_assumptions", "component_selection_need",
            "design_decisions_needed", "missing_inputs", "rationale", "next_stage")


def norm(text: str) -> str:
    """Comparison form: lowercase, unified dashes and quotes, collapsed whitespace."""
    text = str(text).lower()
    for a, b in (("–", "-"), ("—", "-"), ("−", "-"), ("°", " deg "),
                 ("‘", "'"), ("’", "'"), ("“", '"'), ("”", '"'),
                 ("~", " approximately "), ("≈", " approximately ")):
        text = text.replace(a, b)
    return " ".join(re.sub(r"[^\w.\-/%'\"+]", " ", text).split())


def quoted(quote, statement: str) -> bool:
    return isinstance(quote, str) and bool(quote.strip()) and norm(quote) in norm(statement)


def compute_route(signals: dict) -> str:
    blocking = [m for m in signals.get("blocking_missing_inputs") or [] if str(m).strip()]
    if signals.get("objective_clear") is not True or blocking:
        return "INSUFFICIENT_INPUT"
    if signals.get("architecture_state") == "UNRESOLVED" or signals.get("component_function_known") is not True:
        return "DESIGN_LED"
    if signals.get("architecture_state") == "FIXED" and not signals.get("selection_affecting_design_decisions"):
        return "SELECTION_LED"
    return "HYBRID"


def check_route(route: dict, statement: str) -> list[str]:
    problems = []
    if not isinstance(route, dict):
        return ["PROBLEM_ROUTE is not an object"]
    missing = [k for k in REQUIRED if k not in route]
    if missing:
        return [f"missing field(s): {', '.join(missing)}"]
    if route["artifact"] != "PROBLEM_ROUTE":
        problems.append("artifact must be PROBLEM_ROUTE")
    s = route["routing_signals"] if isinstance(route["routing_signals"], dict) else {}
    for key in ("objective_clear", "component_function_known"):
        if not isinstance(s.get(key), bool):
            problems.append(f"routing_signals.{key} must be true or false")
    if s.get("architecture_state") not in ARCHITECTURE_STATES:
        problems.append(f"routing_signals.architecture_state must be one of {ARCHITECTURE_STATES}")
    for key in ("selection_affecting_design_decisions", "blocking_missing_inputs"):
        if not isinstance(s.get(key, []), list):
            problems.append(f"routing_signals.{key} must be a list")
    if route["route"] not in ROUTES:
        problems.append(f"route must be one of {ROUTES}")
    expected = compute_route(s)
    if route["route"] != expected:
        problems.append(f"route {route['route']} disagrees with the routing rules ({expected})")
    if route["next_stage"] != NEXT_STAGE.get(route["route"]):
        problems.append(f"next_stage {route['next_stage']} must be {NEXT_STAGE.get(route['route'])} "
                        f"for {route['route']}")
    # fixed constraints are the user's own: each needs a verbatim quote from the statement
    for i, c in enumerate(route["fixed_constraints"] or []):
        if not isinstance(c, dict) or not quoted(c.get("quote"), statement):
            problems.append(f"fixed_constraints[{i}] has no verbatim quote from the problem statement "
                            "(an unquoted constraint is an assumption, not a fixed constraint)")
    # missing inputs: only blocking ones may drive INSUFFICIENT_INPUT, and they must be listed
    blocking_listed = [m.get("item") for m in route["missing_inputs"] or []
                       if isinstance(m, dict) and m.get("blocks_routing") is True]
    if sorted(map(norm, blocking_listed)) != sorted(map(norm, s.get("blocking_missing_inputs") or [])):
        problems.append("routing_signals.blocking_missing_inputs must equal the missing_inputs marked "
                        "blocks_routing")
    need = route["component_selection_need"] if isinstance(route["component_selection_need"], dict) else {}
    decisions = [d for d in route["design_decisions_needed"] or [] if str(d).strip()]
    if route["route"] == "SELECTION_LED":
        if need.get("needed") is not True or not str(need.get("category") or "").strip():
            problems.append("SELECTION_LED needs component_selection_need.needed true and a category")
        if decisions:
            problems.append("SELECTION_LED must not list design decisions (do not redesign a fixed "
                            "selection problem)")
    if route["route"] in ("DESIGN_LED", "HYBRID") and not decisions:
        problems.append(f"{route['route']} must list the design decisions that come before selection")
    if route["route"] == "HYBRID" and need.get("needed") is not True:
        problems.append("HYBRID means a component is still to be selected after design work")
    if not str(route["rationale"]).strip():
        problems.append("rationale is required")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--route", type=Path, required=True)
    ap.add_argument("--statement", type=Path, required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        route = json.loads(args.route.read_text("utf-8"))
        statement = args.statement.read_text("utf-8")
    except (OSError, ValueError) as exc:
        print(f"INPUT ERROR: {exc}", file=sys.stderr)
        return 2
    problems = check_route(route, statement)
    result = {"check": "PROBLEM_ROUTE", "status": "FAIL" if problems else "PASS",
              "computed_route": compute_route(route.get("routing_signals") or {}) if isinstance(route, dict) else None,
              "problems": problems}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for p in problems:
            print(f"PROBLEM {p}")
        print(f"PROBLEM_ROUTE CHECK: {result['status']} (computed route {result['computed_route']})")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
