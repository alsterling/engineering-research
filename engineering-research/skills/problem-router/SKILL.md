---
name: problem-router
description: Front-end routing for an engineering problem before any product search. Decides whether the problem is SELECTION_LED (architecture fixed; go straight to evidence-graded product selection), DESIGN_LED (the mechanism or architecture is unresolved; design work first), HYBRID (some architecture fixed, but design decisions materially change what to buy), or INSUFFICIENT_INPUT (the physical objective itself is ambiguous). Use when the user asks to route, triage or scope an engineering problem, asks whether a problem needs design work before component selection, or presents a component or equipment need inside a wider system. Returns a PROBLEM_ROUTE. Never searches for or names products. Public/synthetic T0 information only.
---

# Problem Router V1

Decide how an engineering problem should be approached before anyone searches for products.
Selection problems must stay fast; design problems must not be sent straight to product search.

You route. You do not design the system, search for products, name products or select anything.

## Procedure

1. **Objective.** Restate the physical or system objective in one sentence. Set
   `objective_clear` to false only if you cannot tell what physical result is wanted (what must
   move, flow, be measured, protected, held, heated, and so on).
2. **Fixed constraints.** List what the user actually stated as fixed. Each one needs a verbatim
   `quote` from the problem statement. Anything you infer is not a fixed constraint: put it under
   architecture assumptions or uncertain constraints.
3. **Uncertain constraints and assumptions.** List stated values that are approximate, provisional
   or "screening", and the architecture assumptions the problem rests on (`STATED` or `IMPLIED`).
4. **Component.** Is the function of the component or equipment to be selected known? Give its
   category (for example "3-pole motor protection circuit breaker"), or null.
5. **Architecture state.** `FIXED` (the system around the component is settled), `PARTIAL` (a
   system exists, but open design questions remain) or `UNRESOLVED` (the mechanism or
   architecture itself is not decided).
6. **Selection-affecting design decisions.** List only the design decisions that would change what
   is bought: its category, its size or rating class, or the values of its key HARD requirements.
   Leave out ordinary requirements the user has simply not stated yet (pressure rating,
   connections, enclosure and so on). The selection skill's SPEC and G1 gate collect those.
7. **Missing inputs.** List them. Mark `blocks_routing: true` only when the missing item stops
   any responsible route, which in practice means the objective itself is unclear. A missing
   ordinary product requirement never blocks routing.
8. **Route** by these rules (first match wins):
   1. objective not clear, or any blocking missing input → `INSUFFICIENT_INPUT`
   2. architecture `UNRESOLVED`, or component function not known → `DESIGN_LED`
   3. architecture `FIXED` and no selection-affecting design decision → `SELECTION_LED`
   4. otherwise → `HYBRID`
9. **Next stage:** SELECTION_LED → `ENGINEERING_RESEARCH_RUN`; DESIGN_LED → `FIELD_DESIGN_EXPERT`;
   HYBRID → `FIELD_DESIGN_EXPERT_THEN_ENGINEERING_RESEARCH`; INSUFFICIENT_INPUT →
   `CLARIFY_WITH_HUMAN` (ask the specific questions).
10. Output the PROBLEM_ROUTE below. If a shell is available, check it with
    `python skills/problem-router/scripts/route_check.py --route ROUTE.json --statement STATEMENT.txt`.
    Any PROBLEM line means the route is inconsistent: fix it before going on.
11. **STOP** after the route, unless the user asked you to continue:
    - SELECTION_LED: the next step is the `engineering-research` skill (RUN) with the user's
      request. Do not redesign a fixed selection problem.
    - DESIGN_LED or HYBRID: the next step is the `field-design-expert` skill. Never send these
      straight to product search.
    - INSUFFICIENT_INPUT: ask the clarifying questions and wait.

Do not use web search or fetch, and do not invoke the `engineering-research` skill for a
DESIGN_LED or HYBRID problem.

## Output

```json
{
  "artifact": "PROBLEM_ROUTE",
  "version": "1.0",
  "route": "SELECTION_LED | DESIGN_LED | HYBRID | INSUFFICIENT_INPUT",
  "stated_objective": "one sentence",
  "routing_signals": {
    "objective_clear": true,
    "component_function_known": true,
    "architecture_state": "FIXED | PARTIAL | UNRESOLVED",
    "selection_affecting_design_decisions": ["..."],
    "blocking_missing_inputs": ["..."]
  },
  "fixed_constraints": [{"item": "...", "quote": "verbatim from the statement"}],
  "uncertain_constraints": [{"item": "...", "why_uncertain": "..."}],
  "architecture_assumptions": [{"assumption": "...", "status": "STATED | IMPLIED"}],
  "component_selection_need": {"needed": true, "category": "... or null"},
  "design_decisions_needed": ["..."],
  "missing_inputs": [{"item": "...", "blocks_routing": false}],
  "rationale": "why this route, in 2-4 sentences",
  "next_stage": "ENGINEERING_RESEARCH_RUN | FIELD_DESIGN_EXPERT | FIELD_DESIGN_EXPERT_THEN_ENGINEERING_RESEARCH | CLARIFY_WITH_HUMAN"
}
```

`design_decisions_needed` is empty for SELECTION_LED and non-empty for DESIGN_LED and HYBRID.
`blocking_missing_inputs` repeats the items marked `blocks_routing: true`.
