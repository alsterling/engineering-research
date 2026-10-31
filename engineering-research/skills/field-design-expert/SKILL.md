---
name: field-design-expert
description: Design-stage engineering review that runs BEFORE product search when a problem is DESIGN_LED or HYBRID (from the problem-router). Checks whether the system architecture around a component should be accepted as given, challenged or clarified. Identifies fixed constraints versus untested assumptions, first-order design variables, credible architecture options, required calculations, materials, controls, safety and reliability questions, and what is and is not ready for selection. Returns a FIELD_DESIGN_RESULT and a draft ENGINEERING_RESEARCH_HANDOFF for the engineering-research skill, then stops at a human gate. Not product discovery: never searches for, ranks or names products. Public/synthetic T0 information only.
---

# Field/Design Expert V1

Check the system before anyone optimizes the component. Do not redesign without cause: challenge an
assumption only when it materially changes what should be selected, or whether selection should
happen yet.

## Boundaries

- No product discovery: do not use web search or fetch, do not search catalogs, do not name,
  rank or recommend products, vendors or models.
- Do not invent requirements. A value is known only if the user stated it: quote it verbatim.
  Everything else stays `UNKNOWN`. A good engineering default is a question or a calculation to
  run, not a requirement.
- Preserve requirement semantics. Every user number keeps its qualifiers: `APPROXIMATE`
  ("approximately", "about", "~"), `NOMINAL`, `OBSERVED` ("current", "measured", "existing"),
  `SCREENING` ("screening", "considered", "future", "provisional"), or `STATED` when the user
  gives it plainly. Never turn a number into a comparison it did not state: "approximately
  5 L/min" is a reference value, not `>= 5`, `<= 5`, `= 5` or a target, and "55-70 C" stays the
  range as supplied. A number becomes a HARD predicate only if the user wrote the operator next
  to it ("at least 25 kA": `operator_basis` USER_STATED) or a recorded human gate approved it
  (`operator_basis` HUMAN_APPROVED with that gate's decision id as `approval_ref`). Otherwise it
  goes to `reference_values` (no operator) or `unknown_requirements`.
- Do not optimize exhaustively. Do not perform calculations whose inputs are unknown. List them,
  with their inputs and what they decide.
- Do not choose an architecture. When several are materially plausible, keep them all, say what
  each would change, and leave the choice to the human (`OPEN_FOR_HUMAN_DECISION`). Use
  `ACCEPTED_AS_GIVEN` only when the stated architecture holds and nothing material challenges it.
- Never bypass the human gate. Do not invoke the `engineering-research` skill yourself.

## Procedure

Start from the PROBLEM_ROUTE if there is one; otherwise route the problem first with the
`problem-router` skill.

1. **System objective:** the physical or system result that matters (not "replace the part").
2. **Current architecture:** the elements and their order as stated; mark anything inferred.
3. **Fixed constraints:** only what the user stated as fixed, each with a verbatim `quote`.
4. **Assumptions to challenge:** things treated as fixed without evidence (a provisional duty
   point, a loop order, a component type, a control approach). For each: why it matters to
   selection, and how to resolve it.
5. **First-order variables:** the few variables that dominate the design and the selection.
   `current_value` is quoted from the statement or `UNKNOWN`.
6. **Architecture options:** only where justified, each with when it is plausible and how it
   would change the selection. Never mark one as chosen.
7. **Required calculations / criteria:** id (`CALC-1`, ...), what to calculate, the inputs it
   needs, and what it decides.
8. **Questions:** material compatibility; controls and operability; safety and reliability.
   Ask only what could change the design or the selection.
9. **Readiness:** requirements ready for selection (stated by the user, quoted, with value, with
   qualifiers and an operator the user stated), and unresolved requirements (value `UNKNOWN`, with what resolves each: a `CALC-n` id, `HUMAN`,
   `MEASUREMENT` or `VENDOR_DATA`).
10. **Capability needs (optional):** if the work needs a capability you do not have (for example a
    hydraulic calculation tool), list it as a kebab-case tag with why. These go to the
    `capability-resolver` skill. Leave the list empty when nothing is needed.
11. **Handoff:** write the draft ENGINEERING_RESEARCH_HANDOFF below. It contains only what the
    `engineering-research` RUN skill needs. HARD requirements are only user-stated values with an
    operator the user stated (`origin` USER, `basis` GIVEN, `operator_basis` USER_STATED, with the
    quote), or with a recorded human approval. User numbers without a stated operator go to
    `reference_values` with their qualifiers and meaning. Unresolved items go to
    `unknown_requirements`. Status `DRAFT_PENDING_HUMAN_GATE`.
12. If a shell is available, check both artifacts:
    `python skills/field-design-expert/scripts/fde_check.py --result RESULT.json --handoff HANDOFF.json --statement STATEMENT.txt`
    (`--approvals GATE.json` supplies a recorded human gate's decision ids; `--render` prints the
    plain request for the RUN skill; `--resolver-requests DIR` writes Capability Resolver
    requests for the capability needs). Fix every PROBLEM line.
13. **STOP at the human gate.** The human approves or changes the architecture, the
    calculations and the handoff. After approval, a design-derived value may enter the handoff as
    `basis: APPROVED_DESIGN_DECISION` with an `approval_ref`; only then does product research
    start, in the `engineering-research` skill.

## Output 1: FIELD_DESIGN_RESULT

```json
{
  "artifact": "FIELD_DESIGN_RESULT",
  "version": "1.1",
  "problem_route": {"route": "DESIGN_LED | HYBRID | ...", "next_stage": "..."},
  "system_objective": "...",
  "current_architecture": {"description": "...", "elements": ["..."], "source": "STATED | IMPLIED"},
  "fixed_constraints": [{"item": "...", "quote": "verbatim"}],
  "assumptions_to_challenge": [{"assumption": "...", "why_it_matters": "...", "how_to_resolve": "..."}],
  "first_order_variables": [{"variable": "...", "why_first_order": "...", "current_value": "UNKNOWN or quoted value", "qualifiers": ["APPROXIMATE | NOMINAL | OBSERVED | SCREENING | STATED, if known"], "quote": "if known"}],
  "architecture_options": [{"option": "...", "when_plausible": "...", "effect_on_selection": "..."}],
  "architecture_choice": "ACCEPTED_AS_GIVEN | OPEN_FOR_HUMAN_DECISION",
  "required_calculations": [{"id": "CALC-1", "calculation": "...", "inputs_needed": ["..."], "decides": "..."}],
  "material_compatibility_questions": ["..."],
  "controls_operability_questions": ["..."],
  "safety_reliability_questions": ["..."],
  "requirements_ready_for_selection": [{"parameter": "...", "operator": "only as the user stated it", "value": "...", "unit": "...", "qualifiers": ["..."], "operator_basis": "USER_STATED | HUMAN_APPROVED", "quote": "verbatim, contains the value and the operator words"}],
  "unresolved_requirements": [{"parameter": "...", "value": "UNKNOWN", "why_unresolved": "...", "resolved_by": "CALC-1 | HUMAN | MEASUREMENT | VENDOR_DATA"}],
  "capability_needs": [{"tag": "kebab-case-capability", "why": "..."}],
  "recommended_next_step": "...",
  "human_gate_required": "YES"
}
```

## Output 2: ENGINEERING_RESEARCH_HANDOFF (draft)

```json
{
  "artifact": "ENGINEERING_RESEARCH_HANDOFF",
  "version": "1.1",
  "status": "DRAFT_PENDING_HUMAN_GATE",
  "selection_objective": "...",
  "component_category": "...",
  "approved_architecture_context": "the architecture as stated, with what is still pending approval",
  "hard_requirements": [{"id": "H1", "parameter": "...", "operator": "as stated by the user", "value": "...", "unit": "...", "condition": "...", "safety_critical": "YES | NO | UNKNOWN", "origin": "USER", "basis": "GIVEN", "qualifiers": ["..."], "operator_basis": "USER_STATED | HUMAN_APPROVED", "approval_ref": "only with HUMAN_APPROVED", "quote": "verbatim, contains the value"}],
  "reference_values": [{"parameter": "...", "value": "...", "unit": "...", "qualifiers": ["APPROXIMATE", "OBSERVED"], "semantics": "e.g. current observed reference flow; not a limit", "quote": "verbatim"}],
  "soft_preferences": [{"parameter": "...", "preference": "...", "origin": "USER", "quote": "verbatim"}],
  "unknown_requirements": [{"parameter": "...", "value": "UNKNOWN", "why_unknown": "...", "resolve_by": "..."}],
  "required_evidence_types": ["e.g. manufacturer performance curve at the stated fluid temperature"],
  "known_constraints": [{"item": "...", "quote": "verbatim"}],
  "excluded_assumptions": ["assumptions the search must not carry forward"],
  "approved_search_scope": {"in_scope": ["..."], "out_of_scope": ["..."]},
  "data_tier": "T0"
}
```
