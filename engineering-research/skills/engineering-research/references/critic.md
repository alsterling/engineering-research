# REFERENCE: SECOND-MODEL CRITIC

Production rule text, verbatim. `../SKILL.md` governs loading; its rules apply
alongside.

Also load: `evidence.md` for a critic job, applying a finding and a PROPAGATION
REVIEW; `certification.md` for a certification/approval predicate;
`discovery.md` if C3 fires; `soft-enrich.md` before a SOFT ENRICH ADDENDUM or
re-ranking.

---

Contents:
- CRITIC INDEPENDENCE
- CRITIC MODE - TWO JOBS ONLY
- JOB 2 ELIGIBILITY
- CRITIC_RESULT CONTRACT
- CRITIC FINDING TYPES
- CRITIC OUTCOME ENFORCEMENT
- CRITIC FINDING PROPAGATION

---

## CRITIC INDEPENDENCE

Why: the accepted M9-B critic ran in a fresh session on the same model as the
primary run; "different strong model/session" did not say whether that counted
or how to record it.

Independence has three dimensions, recorded separately; there is no single
independent yes/no:
- session: FRESH_SESSION (a session that has not participated in the primary
  run) | SAME_SESSION | UNKNOWN_SESSION
- model family (critic_family): CROSS, a materially different model family or
  provider lineage from the primary run, where the recorded metadata
  establishes it | SAME, the same family, even in a different session or with a
  different temperature, reasoning mode or tool mode | UNKNOWN, the metadata
  does not establish it
- context: BRIEF_ONLY, the critic works only from the CRITIC_BRIEF and the
  material it includes or references | ADDITIONAL_PRIOR_CONTEXT, it also has
  primary-run reasoning or conclusions, earlier critic attempts, unrelated
  project context or memory not in the brief | UNKNOWN_CONTEXT
A different model family in the same session, or with uncontrolled prior
conclusions, is not independent merely because the model differs. The same
family in a fresh, brief-only session is weaker than CROSS but stronger than the
same session.

independence_quality is derived from the recorded dimensions and never claims
more than the metadata supports:
- STRONG: FRESH_SESSION, BRIEF_ONLY and CROSS
- ACCEPTABLE_WITH_LIMITATION: FRESH_SESSION with BRIEF_ONLY and a SAME or
  UNKNOWN family, or with ADDITIONAL_PRIOR_CONTEXT the critic does not rely on
- INSUFFICIENT: SAME_SESSION; a critic that materially relies on uncontrolled
  prior-run context; or recorded metadata that contradicts the claimed session
  or family, for example the same session ID, or the same recorded family
  called CROSS
- UNKNOWN: the session or the context cannot be established

Record with the CRITIC_RESULT: primary_model; primary_model_family when known;
primary_session_id or "not available"; critic_model; critic_model_family when
known; critic_session_id or "not available"; session_independence;
critic_family; context_independence; independence_quality;
independence_reason. Identifiers a platform does not expose are recorded as
"not available"; the classification then reflects that uncertainty.

The CRITIC_BRIEF also states the primary model and family when known, the
primary session identifier when available, the independence target (CROSS when
practically available, otherwise a SAME-family fresh session), and that the
critic works from the brief, not from unseen primary-run context.

Use: run the critic in a FRESH_SESSION with BRIEF_ONLY context, CROSS when
practically available. A fresh, brief-only SAME or UNKNOWN family critic meets
the handoff above and is applied as ACCEPTABLE_WITH_LIMITATION, with the
limitation stated alongside the critic outcome at G2. If the quality is
INSUFFICIENT or UNKNOWN, record CRITIC_INDEPENDENCE_INSUFFICIENT, do not apply
the result as the run's critic pass, and STOP at the critic handoff; the human
may supply the missing metadata, approve another critic pass or skip the
critic.

Independence is separate from correctness: an independent critic can still be
wrong (invalid findings are handled by CRITIC FINDING TYPES and JOB 2
ELIGIBILITY), and correct findings do not prove independence. Independence
never changes requirement statuses, finding validity or the meaning of C1-C4.
These tokens are metadata, not requirement statuses or evidence grades.

## CRITIC MODE - TWO JOBS ONLY

Job 1: attack the leader.
- try to disqualify or downgrade it on current manufacturer evidence
- check configuration, operating conditions, manuals, footnotes, certifications,
  semantic mismatches, derived values, and authoritative contradictions

Job 2: one missed-family check.
- examine ONE family/candidate that is eligible under JOB 2 ELIGIBILITY below
- prefer sibling/successor/newer/higher-capacity family or uncovered
  manufacturer
- check discriminating HARD requirements first
- stop that branch at the first HARD FAIL

Critic must not:
- change SPEC
- add requirements
- rerank with different SOFT priorities
- redo the full market search

## JOB 2 ELIGIBILITY

A Job 2 family/candidate is eligible only if the primary run did not already
evaluate it:
- UNCOVERED: not in the primary run's discovery coverage
- LOGGED_UNSCREENED: logged as a lead, reserve, sibling or plausible option, but
  not advanced to EXTRACT, not excluded by an evidence-supported HARD mismatch,
  and not already given the full HARD evaluation Job 2 would perform

Ineligible:
- ALREADY_ADVANCED: advanced to EXTRACT / CHECK
- EVIDENCE_EXCLUDED: rejected by an evidence-supported HARD mismatch
- DUPLICATE_IDENTITY: an evaluated candidate/configuration under another
  spelling, URL, distributor listing or alias; a different source is not a
  different candidate
- FULLY_EVALUATED: a reserve or sibling that already received the full HARD
  evaluation

Appearing in DISCOVERY_LOG does not by itself make a family ineligible, and
family-name equality alone does not disqualify. A different exact configuration
of an evaluated family, or a different suffix or option code, is eligible only
if it was not itself fully evaluated and the difference could materially change
HARD compliance; EXPLICIT APPLICABILITY decides whether a source covers it.

The CRITIC_BRIEF includes a primary-run identity ledger that marks each logged
family/candidate ADVANCED, EVIDENCE_EXCLUDED or LOGGED_UNSCREENED, with stable
identities and the aliases the run knows. A family absent from the ledger is
UNCOVERED.

The critic records eligibility_class and eligibility_basis: the ledger entry, or
its absence, that makes the choice eligible. If eligibility cannot be
established from the brief, Job 2 is JOB2_NOT_COMPLETED with reason
ELIGIBILITY_NOT_ESTABLISHED.

An ineligible Job 2 selection is contract-invalid for Job 2: it is not a missed
family, cannot support C3 and triggers no coverage repair. Record the
invalidity; a valid Job 1 result still stands.

## CRITIC_RESULT CONTRACT

The CRITIC_BRIEF gives the critic this contract as its required output. The
CRITIC_RESULT reports these fields in this order. Every status field uses
exactly one canonical requirement status. The primary run records a missing
field as missing and does not fill it in for the critic.

Run identity:
- run_id
- critic_session_id, or "not available"
- critic model / platform / mode, as reported
- critic_family: SAME | CROSS | UNKNOWN, relative to the primary run, with the
  other CRITIC INDEPENDENCE fields

JOB 1 - attack the leader:
- leader candidate and exact configuration
- either one block per finding, or JOB1_NO_HARD_STATUS_CHANGE with the
  documents/evidence examined
- each finding: finding_id (stable, for example J1-F1), requirement_id (in the
  frozen SPEC), old_status, new_status, finding_type (EVIDENCE | RULE_ONLY | SEMANTIC_INTERPRETATION),
  rule_applied, evidence_refs (required for both types; CRITIC FINDING TYPES),
  reason

JOB 2 - one missed-family check:
- family examined, and the exact candidate/configuration or "not resolved"
- why this family was chosen
- eligibility_class (UNCOVERED | LOGGED_UNSCREENED) and eligibility_basis, under
  JOB 2 ELIGIBILITY
- HARD requirement IDs in the order checked, with evidence_refs
- result: JOB2_HARD_FAIL | JOB2_NO_HARD_FAIL | JOB2_NOT_COMPLETED (with its
  reason, for example ELIGIBILITY_NOT_ESTABLISHED)
- JOB2_HARD_FAIL: first failing requirement_id, required predicate, actual
  evidence-supported value/state, evidence_ref, stop point
- JOB2_NO_HARD_FAIL: requirement_id, status and evidence_refs for every frozen
  HARD requirement

Enforcement fields, all four present:
- C1: YES | NO, C1_basis: finding IDs or NONE
- C2: YES | NO, C2_basis: finding IDs or lane-transition reference, or NONE
- C3: YES | NO, C3_basis: Job 2 candidate and evidence-completeness reference,
  or NONE
- C4: YES | NO, C4_basis: explicit basis or NONE
- advisory_outcome_label: exactly one of labels 1-4 below, number and text,
  consistent with the reported C1-C4

Evidence references:
- evidence_refs point by stable ID (for example D1) to evidence rows in the
  CRITIC_RESULT's own evidence section; each row carries the HARD PASS
  TRACEABILITY fields and states whether the primary run already had it
- never an unnamed source, "manufacturer data", an untraceable search result or
  an unsupported prose assertion

The critic's C1-C4 fields and label are advisory, like any critic label; the
primary run applies CRITIC OUTCOME ENFORCEMENT to the findings. This contract
fixes the shape of the result only.

## CRITIC FINDING TYPES

EVIDENCE: the change rests on new or different evidence, for example a newly
retrieved authoritative source or a corrected extraction.

RULE_ONLY: no new evidence. The critic applies the frozen SPEC and the current
skill rules to evidence the primary run already had and shows that the recorded
HARD status was wrong. Examples: PASS -> UNKNOWN because the document-set rule
was misapplied; CONDITIONAL -> PASS because the checked evidence already met the
predicate; PASS -> FAIL because recorded evidence clearly violated it.

A RULE_ONLY finding is valid only if it gives the candidate/configuration, the
frozen requirement_id, old and new canonical statuses, evidence_refs to evidence
the primary run already had, the exact SPEC/skill rule applied and a concise
reason. It is invalid if it adds a requirement, strengthens or weakens a frozen
requirement, promotes a watchlist item into HARD, invents a missing condition,
reinterprets the user's intent beyond the frozen SPEC or relies on unrecorded
evidence. An invalid finding is not applied and is not C1.

C1 fires for a valid finding of either type that changes the canonical status of
a HARD requirement of an evaluated candidate in the current CHECK_RESULT. C1 does
not fire when only wording, a note or rationale, an evidence grade, a SOFT field
or the ranking changes, when the critic only recommends more research, or when
the finding is invalid. A C1 change may or may not change a lane; C2 keeps its
own definition.

SEMANTIC_INTERPRETATION: no new evidence; the change rests on how the frozen
predicate's own wording is read rather than on a skill rule. It is valid only
under the RULE_ONLY validity conditions and must quote the frozen predicate text
it reads. It may not reinterpret the user's intent beyond the frozen SPEC. The
type never changes validity, C1-C4 or the outcome label; it is shown with the
finding at G2 so the human sees which status changes are readings of SPEC
wording.

## CRITIC OUTCOME ENFORCEMENT

Critic prose labels are advisory. Findings control workflow state.

Apply every rule that fires:

C1 - HARD STATUS CHANGE
If a valid critic finding, EVIDENCE or RULE_ONLY (CRITIC FINDING TYPES), changes
any HARD status for any existing candidate:
- create CHECK_RESULT_vN+1
- run the PROPAGATION REVIEW (CRITIC FINDING PROPAGATION) and record its
  corrections in CHECK_RESULT_vN+1

C2 - LANE CHANGE
If any lane changes:
- apply C1 update
- log the lane change

C3 - MISSED QUALIFYING CANDIDATE / COVERAGE FAILURE
A missed family reopens coverage only when the critic evidence supports PASS for
every frozen HARD requirement under this skill's normal CHECK rules.

SOFT price, stock, or lead time never decide whether C3 fires.

If C3 fires:
- add that family/candidate to EXTRACT using the critic evidence
- mark coverage as failed for the bounded run
- run ONE COVERAGE REPAIR pass using the same DISCOVERY ROUTE, focused on the
  uncovered/missed portion of the market rather than redoing the full search
- the repair may advance at most 5 additional plausible candidates and inspect at
  most 15 additional verification source records
- update EVIDENCE_TABLE and CHECK_RESULT before any replacement MEMO

The critic-found candidate counts inside the repair limit only if extra research
beyond the critic evidence is needed.

Any C1, C2, or C3:
- current DECISION_MEMO = SUPERSEDED

C4 - BOUNDED RESULT SURVIVES
Only if none of C1-C3 fired.

Primary outcome label (apply mechanically):
1. LEADER DISQUALIFIED - reopen CHECK
   - use only when a valid critic finding gives the current preferred candidate at
     least one HARD FAIL, so its lane becomes EXCLUDED
2. LEADER NOT DISQUALIFIED, BUT HARD STATE CHANGED - reopen CHECK
   - use when label 1 does not apply and C1 or C2 fires, including PASS ->
     CONDITIONAL / CONFLICT / UNKNOWN or a resulting move to VERIFY FIRST
3. MATERIAL MISSED QUALIFYING CANDIDATE FOUND - reopen coverage
   - use when neither label 1 nor label 2 applies and C3 fires
4. LEADER SURVIVES AND NO MATERIAL MISSED QUALIFYING FAMILY FOUND - bounded
   result survives
   - use only when none of C1-C3 fires

If more than one rule fires:
- report every fired rule
- choose the lowest-numbered applicable outcome label under the mechanical rules
  above

A leader moving from SPECIFY NOW to VERIFY FIRST because of CONFLICT, CONDITIONAL,
or UNKNOWN is not label 1; it is label 2 unless a HARD FAIL also makes it EXCLUDED.

After applying critic findings and any required COVERAGE REPAIR:
- if the qualifying set changed, run a bounded SOFT ENRICH ADDENDUM for newly
  qualifying candidates before re-ranking
- issue the replacement MEMO if required
- proceed to G2
- do not run a second critic without human approval

## CRITIC FINDING PROPAGATION

Why: a critic correction applied only to the leader can leave the same known
rule or evidence error in other candidates of the same run.

For each valid finding applied under C1 (the originating finding), the reopened
CHECK runs one PROPAGATION REVIEW: does the same correction apply to a HARD
requirement of another candidate already evaluated in this run?

The review is bounded to all of:
- other candidates/configurations already in the current CHECK_RESULT
- frozen HARD requirements already in the SPEC
- evidence already in the run's EVIDENCE_TABLE or the CRITIC_RESULT; a critic
  evidence row covers another candidate only under EXPLICIT APPLICABILITY
- the rule or evidence interpretation the originating finding corrected
It is not discovery and allows no new retrieval, search or research.

A candidate/HARD cell is a plausible target when its recorded status rests on
the same rule application, evidence interpretation, status-contract treatment or
document-state treatment that the originating finding corrected. Examples: PASS
allowed although the applicable certification/declaration record was not
retrieved; an unresolved model-pattern qualifier treated as explicitly
applicable; the same decorated or judgment-dependent status treatment;
EXISTS_NOT_RETRIEVED treated as though the document had been inspected.

Not a basis: shared manufacturer, family, name, voltage, size, wattage or other
attribute; another candidate's FAIL or lane change; a critic concern without a
valid finding. Candidate-specific evidence stays candidate-specific; only the
same rule/evidence-processing defect propagates.

Record one review outcome for every cell examined. Review outcomes are not
requirement statuses and never replace PASS, FAIL, CONDITIONAL, CONFLICT or
UNKNOWN.
- APPLIES: the same correction clearly applies on evidence already held.
  Re-evaluate that requirement under the frozen SPEC and this skill and record
  the corrected canonical status in CHECK_RESULT_vN+1.
- DOES_NOT_APPLY: the held evidence or the rules clearly show it does not apply.
  The status is unchanged.
- NOT_DETERMINABLE: the held evidence cannot decide it. The status is unchanged;
  do not force PASS or FAIL and do not research it here. Record why, and list it
  in the replacement memo's exceptions/risks as an open verification need.

Propagation record, one per examined cell: originating finding_id, originating
candidate, originating requirement_id, target candidate, target requirement_id,
review outcome, evidence refs reviewed, rule applied, old canonical status, new
canonical status (APPLIES only), concise reason. If no cell is a plausible
target, record NO_PROPAGATION_TARGETS. Never skip a plausible target silently.

The originating finding stays the only critic finding: propagated corrections
cite it, create no new critic findings and do not re-decide C1. Lane and memo
consequences follow CANDIDATE LANES and CRITIC OUTCOME ENFORCEMENT unchanged.

The review stops when every plausible target has a record. It adds no
candidate, family or requirement, hunts no source, and does not propagate from a
propagated correction or a speculative concern. A propagated correction may
change a status or lane; it starts no further research cycle.

