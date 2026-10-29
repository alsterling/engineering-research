# REFERENCE: NONE FOUND SUMMARY

Production rule text, verbatim. `../SKILL.md` governs loading; its rules apply
alongside.

Also load: `evidence.md` to describe a blocker; `verify-action.md` before
naming VERIFY ACTION or DIRECT VERIFICATION PROPOSAL as a next action;
`retrieval-fallback.md` before naming
RETRIEVAL FALLBACK as a next action; `human-supplied-evidence.md` before naming
HUMAN-SUPPLIED EVIDENCE as a next action; `critic.md` when a critic result was
applied in the run.

---

Contents:
- NONE FOUND SUMMARY

---

## NONE FOUND SUMMARY

Why: a NONE FOUND memo can list nearest misses without saying what blocks them
or what, if anything, could move one forward.

NONE FOUND means: within the frozen SPEC, the bounded discovery and verification
scope, the evidence available to this run and the applicable budgets, zero
evaluated candidates currently qualify for SPECIFY NOW. It does not mean that no
compliant product exists, that the market has no solution, that every candidate
failed, that every UNKNOWN is a failure, or that further evidence could not
change the result.

When the SPECIFY NOW count is 0, memo item 2 is NONE FOUND and the memo contains
a NONE_FOUND_SUMMARY, which supplies items 6-8 for the nearest candidates:
- outcome: NONE FOUND
- scope_statement: the bounded run scope
- specify_now_count (0), verify_first_count, excluded_count
- nearest_candidates
- blocking_requirements for each nearest candidate
- next_action for each blocker, or NO_BOUNDED_NEXT_ACTION
- coverage_caveat: what the bounded run did and did not establish

Nearest candidates come only from the current CHECK_RESULT, from candidates with
a status for every frozen HARD requirement, using the HARD matrix and lanes,
never SOFT preferences or a score:
1. VERIFY FIRST before EXCLUDED
2. then the fewest blockers to SPECIFY NOW: HARD requirements that are not PASS,
   plus unresolved PRE-SPECIFY-NOW CHECK items not already explained by such a
   requirement
3. candidates with the same number of blockers are all reported; their status
   types are reported, not ranked
If every evaluated candidate is EXCLUDED, report the least-blocked ones as
NEAREST EXCLUDED and state that each has at least one evidence-supported HARD
FAIL. "Nearest" is diagnostic only: never preferred, selected, qualified or
recommended for purchase.

Blocker record, one per blocker of each nearest candidate: candidate;
requirement_id (or the PRE-SPECIFY-NOW CHECK item); canonical status; frozen
predicate in short form; the exact blocker; evidence_refs; document state,
authority or applicability issue where relevant; resolvability
BOUNDED_ACTION_AVAILABLE | HUMAN_EVIDENCE_COULD_RESOLVE | SPEC_CHANGE_REQUIRED |
NO_BOUNDED_ACTION_IDENTIFIED. A PASS requirement is never a blocking
requirement. Describe each status in its own terms:
- FAIL: existing applicable evidence contradicts the frozen HARD predicate
- UNKNOWN: qualification is not established; the evidence is insufficient,
  unretrieved, inaccessible, inapplicable or otherwise unresolved
- CONDITIONAL: state the exact unresolved condition
- CONFLICT: authoritative evidence conflicts, so the requirement cannot be PASS
Never describe UNKNOWN, CONDITIONAL or CONFLICT as failed.

Next action: report, never execute, the smallest legitimate next action the
current workflow already supports:
- VERIFY ACTION, when its conditions are met, including condition 1 (an
  applied critic finding or its PROPAGATION REVIEW); a proposal only, no
  approval is created here
- DIRECT VERIFICATION PROPOSAL, when the blocker meets VERIFY ACTION
  conditions 2-5 but not condition 1: name the one verification question and
  the one direct operation on the identified record or official source. It is
  not a VERIFY ACTION, has no VERIFY ACTION record and creates no approval; it
  executes only if the human explicitly approves that one operation at G2, as
  approved research limited to it
- RETRIEVAL FALLBACK, only for an approved VERIFY ACTION its conditions allow
- HUMAN-SUPPLIED EVIDENCE: the human independently obtains an identified record
  the run could not inspect and supplies it; ACCESS BOUNDARY applies, so the
  run never logs in
- SPEC DECISION REQUIRED: qualification depends on changing a frozen
  requirement; a dependency, not a recommendation; only the human reopens SPEC
- NO_BOUNDED_NEXT_ACTION: no specific, legitimate action is identifiable
A next action names the record, question or requirement it concerns; "research
more", "search more", "investigate further" or "find more products" is not one.
A FAIL is never presented as resolvable by more evidence.

STANDARD VERIFICATION ACTIONS: memo item 8 takes, for each non-PASS HARD
status, the action of its reason code (SKILL.md NON-PASS REASON CODES). The
next-action class is always one of the existing classes above.

| Reason code | Next-action class | Standard action |
|---|---|---|
| NOT_STATED | HUMAN-SUPPLIED EVIDENCE | the human obtains a manufacturer statement for the exact configuration (the run sends no RFQ) |
| DOC_EXISTS_NOT_RETRIEVED | VERIFY ACTION after an applied critic finding, otherwise DIRECT VERIFICATION PROPOSAL | retrieve and inspect the identified record |
| DOC_ACCESS_GATED | HUMAN-SUPPLIED EVIDENCE | the human independently retrieves the gated record and supplies it |
| QUALIFIER_UNRESOLVED, APPLICABILITY_UNRESOLVED | VERIFY ACTION or DIRECT VERIFICATION PROPOSAL; HUMAN-SUPPLIED EVIDENCE if the source is gated | resolve the named qualifier or scope in the authoritative source |
| GRADE_C_ONLY, EQUIVALENCE_UNPROVEN | VERIFY ACTION or DIRECT VERIFICATION PROPOSAL | retrieve the manufacturer-primary source for the same value |
| DERIVED_NOT_QUALIFYING | HUMAN-SUPPLIED EVIDENCE | a manufacturer-stated value or behaviour |
| CONFIG_BELOW_LEVEL_3, OPTION_COEXISTENCE | VERIFY ACTION or DIRECT VERIFICATION PROPOSAL | configurator or manufacturer confirmation of the exact configuration |
| AUTHORITATIVE_CONFLICT | HUMAN-SUPPLIED EVIDENCE | manufacturer clarification; both revisions recorded |
| ROUNDING_FLIP, OTHER_CONDITION, NOT_EVALUABLE | SPEC DECISION REQUIRED | human engineering decision at G2, with both numbers or the condition shown |

Execution rules are unchanged. A VERIFY ACTION stays critic-gated and approved
per operation. A DIRECT VERIFICATION PROPOSAL stays report-only. The run never
logs in, sends RFQs or purchases.

Coverage caveat: state the bounded scope and what limited it, for example
coverage targets not reached, a decisive record ACCESS_GATED, a budget or human
limit reached, or no critic run. NONE FOUND reflects the state after any C3
COVERAGE REPAIR; by itself it never triggers discovery, coverage repair or new
research.

---

