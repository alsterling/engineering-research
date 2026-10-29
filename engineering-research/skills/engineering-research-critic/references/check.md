# REFERENCE: CHECK

Production rule text, verbatim. `../SKILL.md` governs loading; its rules apply
alongside.

Also load: `evidence.md`.

---

Contents:
- 5 - CHECK
  - CANONICAL REQUIREMENT STATUSES
  - NON-PASS REASON CODES
  - HARD PASS TRACEABILITY
  - PRE-SPECIFY-NOW CHECK
- EXACT CONFIGURATION RULE

---

# 5 - CHECK

CHECK consumes only:
- latest SPEC_vN
- latest EVIDENCE_TABLE

Statuses:
PASS
FAIL
CONDITIONAL
CONFLICT
UNKNOWN

PASS
- ordinary HARD: valid A/B evidence satisfies the predicate, or derived evidence
  satisfies the DERIVED-EVIDENCE RULE
- safety-critical HARD: Grade A required unless SPEC_vN says otherwise

FAIL
- evidence clearly violates the approved predicate

CONDITIONAL
- appears compliant only on Grade C evidence
- depends on derived evidence that does not meet the derived rule
- applies only under another condition
- depends on unresolved configuration/order-option coexistence

CONFLICT
- current applicable authoritative evidence disagrees

UNKNOWN
- required evidence is missing or cannot be evaluated without unsupported
  assumption

## CANONICAL REQUIREMENT STATUSES

The only valid requirement status tokens are exactly:
PASS
FAIL
CONDITIONAL
CONFLICT
UNKNOWN

A status field or cell contains exactly one of these five tokens and nothing
else. Do not abbreviate, decorate, qualify, footnote, or append markers to a
status token.

Invalid status tokens include:
- PASS(J)
- PASS (J)
- PASS???
- P(B)
- UNK
- COND

If a row does not satisfy the PASS rules, do not preserve PASS by adding a
qualifier or judgment marker. Assign the canonical non-PASS status the existing
CHECK rules require.

This rule fixes the status vocabulary and representation only. The definitions
above still decide which status applies.

Explanations such as judgment-dependent, derived, caveat, footnote, provenance
note or interpretation note belong in the evidence, note or rationale field or
in surrounding prose, never inside the status token.

A PASS that rests on a reading of the frozen predicate or of the evidence that
a reasonable reviewer could make differently records judgment_dependent: YES
and a one-line judgment_basis in its CHECK_RESULT cell. The status token stays
PASS. The CRITIC_BRIEF lists the leader's judgment-dependent PASS cells first
and Job 1 examines them first. judgment_dependent never changes a status, a
lane or C1-C4.

## NON-PASS REASON CODES

Every HARD status other than PASS records exactly one reason code. The code
explains the status; it never replaces or qualifies the status token.

FAIL: EVIDENCE_VIOLATES
CONDITIONAL: GRADE_C_ONLY | DERIVED_NOT_QUALIFYING | ROUNDING_FLIP |
  OTHER_CONDITION | CONFIG_BELOW_LEVEL_3 | OPTION_COEXISTENCE |
  EQUIVALENCE_UNPROVEN
CONFLICT: AUTHORITATIVE_CONFLICT
UNKNOWN: NOT_STATED | DOC_EXISTS_NOT_RETRIEVED | DOC_ACCESS_GATED |
  QUALIFIER_UNRESOLVED | APPLICABILITY_UNRESOLVED | NOT_EVALUABLE

Each code names an existing rule: Grade C only, the DERIVED-EVIDENCE RULE
(including Rounding), "applies only under another condition", the EXACT
CONFIGURATION RULE, option coexistence, TRACEABLE CROSSWALKS, the
AUTHORITATIVE-CONFLICT RULE, DOCUMENT STATES, UNRESOLVED QUALIFIER, EXPLICIT
APPLICABILITY, and "cannot be evaluated without unsupported assumption".

## HARD PASS TRACEABILITY

A HARD PASS requires:
- URL
- authority
- exact/family scope
- document type
- date/revision when available
- locator
- supporting text/value
- condition
- retrieval date
- derived calculation and inputs when applicable

A row missing URL, locator, supporting value/text, or required derived
calculation cannot support PASS.

## PRE-SPECIFY-NOW CHECK

Before assigning SPECIFY NOW:
- applicable manufacturer document types were checked or their absence handled
  by the MANUFACTURER DOCUMENT SET rule
- no checked document contradicts any HARD PASS
- installation/manual restrictions do not invalidate a datasheet rating
- all derived values satisfy the derived rule
- configuration level is sufficient

Anything unresolved -> VERIFY FIRST.

---

# EXACT CONFIGURATION RULE

Record one level per candidate:

1. FAMILY EXISTS
2. REQUESTED CONFIGURATION APPEARS AVAILABLE
3. REQUESTED CONFIGURATION IS VERIFIED
4. EXACT ORDERING CODE / MPN IS VERIFIED

A HARD requirement met only through an option not verified at level 3 is
CONDITIONAL.

SPECIFY NOW requires at least level 3 for all HARD configuration-dependent
predicates.

Level 4 is normally a procurement-readiness item unless SPEC explicitly makes
exact MPN a HARD requirement.

---

