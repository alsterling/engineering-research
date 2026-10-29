# REFERENCE: INTAKE AND SPEC

Production rule text, verbatim. `../SKILL.md` governs loading; its rules apply
alongside.

Also load: `certification.md` for a HARD certification/approval predicate.

---

# 1 - INTAKE

Capture:
- engineering objective
- product/component category
- application context
- known requirements
- preferences
- procurement region/market when price or availability matters
- target quantity when price or availability matters
- data tier

Do not begin product research.

---

# 2 - SPEC

Convert the request into checkable predicates.

Each requirement must contain:
- stable requirement ID
- parameter
- operator
- value
- unit
- operating/reference condition
- HARD or SOFT
- safety-critical YES/NO
- origin: USER or AI-PROPOSED
- rationale

For a HARD certification/approval predicate, also record authority_of_record:
MANUFACTURER_EVIDENCE_REQUIRED (only MANUFACTURER-PRIMARY evidence satisfies
it; a CERTIFIER-PRIMARY record may corroborate) or EITHER (default; CERTIFICATION
EVIDENCE AUTHORITY applies unchanged).

Example: `references/rationale-and-examples.md` (non-normative).

Never name products during SPEC unless the user supplied a reference product.

Do not substitute a nearby engineering concept for the requested one.
Examples:
- sealed gauge is not the same as true vented gauge
- BFSL/reference accuracy is not Total Error Band
- operating range is not automatically the same as performance/accuracy range
- a nearby pressure/range/configuration is not the requested configuration

## Forgotten requirements

AI may propose requirements the user may have forgotten.

Keep them separate as AI-PROPOSED.

Never silently promote them into the approved SPEC.

## Soft-priority order

If multiple SOFT requirements exist, ask the human to approve their priority
order at G1 before seeing product results.

Do not invent weights.

---

## Research-mode timing

Do not spend a deep-research/discovery mode on INTAKE, SPEC, or G1 merely because
the later market route may benefit from it. Those stages define and approve the
problem; they do not require product discovery.

When the platform exposes research mode as a selectable resource, the recommended
operator sequence is:
1. use ordinary chat/reasoning through explicit G1 approval
2. freeze SPEC_vN
3. then enable the research mode appropriate to the DISCOVERY ROUTE

For OPEN INDUSTRIAL MARKET, after G1 prefer a strong deep-research/discovery mode
when available. For STRUCTURED COMPONENT MARKET and NARROW / KNOWN MARKET, follow
the route rules below.

If deep research was already invoked before G1, the G1 STOP still controls: do not
begin product discovery until the human explicitly approves. A pre-G1 research-mode
invocation is not approval and must not alter or expand SPEC.

---

