# REFERENCE: POST-CRITIC VERIFY ACTION

Production rule text, verbatim. `../SKILL.md` governs loading; its rules apply
alongside.

Also load: `evidence.md`; `critic.md` when a critic result was applied in the
run; `human-supplied-evidence.md` when the human supplies the record.

---

## POST-CRITIC VERIFY ACTION

Why: after critic application a run can stop on one known, unread record; an
open-ended "verify it" then becomes a new research pass.

A VERIFY ACTION is one explicitly described verification step for one HARD
blocker left after critic application. Propose one only when all hold:
1. an applied critic finding or its PROPAGATION REVIEW left a frozen HARD
   requirement of an evaluated candidate unresolved (a non-PASS status, or a
   NOT_DETERMINABLE review outcome)
2. the blocker is a specific, identifiable fact and one bounded verification
   question can be stated
3. one direct operation on an already-identified record or official source
   could materially resolve it, for example: retrieve and inspect one
   identified certificate, declaration of conformity, registry record or
   manual; resolve one known footnote/qualifier from its identified
   authoritative source; check one known exact configuration in an official
   product system
4. no SPEC change, new discovery or new requirement is needed
5. the action stays inside ACCESS BOUNDARY

Otherwise record NO_BOUNDED_VERIFY_ACTION (a workflow result, not a status),
for example when there is no specific blocker, no record is identified
(NOT_IDENTIFIED), the issue needs broad discovery, a SPEC change or "more
research", only a SOFT preference would improve, the requirement already has
sufficient evidence for its status, or the candidate is EXCLUDED by a HARD FAIL
the action cannot affect.

VERIFY ACTION record: verify_action_id; trigger (finding_id and/or propagation
record); candidate (exact configuration); requirement_id; current_status;
current_lane; blocker; verification_question; target_record (the identified
record/source, or "not specifically identified", which means
NO_BOUNDED_VERIFY_ACTION); proposed_action (one operation);
expected_resolution; approval_status PROPOSED | APPROVED | DECLINED;
execution_status NOT_EXECUTED | EXECUTED_RESOLVED | EXECUTED_UNRESOLVED;
acquisition (RUN or HUMAN-SUPPLIED); evidence_refs; document_state_before and
document_state_after when a document is involved; old_status; new_status if
changed; result_reason. These are workflow-control fields, not requirement
statuses.

Approval gate: a VERIFY ACTION is a proposal. Present proposals with the G2
package and STOP. Execute an action only after the human explicitly approves
that action; silence, low cost, public availability or ease are not approval.
If declined, record VERIFY_ACTION_DECLINED and keep the requirement status,
lane and memo outcome; declining is not a FAIL.

Execution, direct action only:
- perform only the approved operation on the approved target
- ACCESS BOUNDARY controls; if authentication is needed, record ACCESS_GATED
  and stop the action
- if the operation fails or the record is unavailable, do not try mirrors,
  copies, other registries, filenames, guessed IDs or further searches;
  alternate retrieval is not part of a VERIFY ACTION
- an unresolved action is never followed automatically by another; a new
  action for the same blocker is a new proposal that needs its own approval

Results:
- retrieval alone decides nothing: inspect the record, set its state under
  DOCUMENT STATES (EXISTS_NOT_RETRIEVED becomes RETRIEVED only when the record
  is inspected; ACCESS_GATED stays ACCESS_GATED unless the human supplies the
  record), then re-evaluate the requirement under the frozen SPEC and the
  existing evidence, authority and applicability rules
- EXECUTED_RESOLVED: the inspected evidence answers the verification question.
  Add it to EVIDENCE_TABLE, record old -> new canonical status in a new
  CHECK_RESULT version, and recompute the lane and memo under CANDIDATE LANES,
  PRE-SPECIFY-NOW CHECK and the existing supersession rules. The new status may
  be non-PASS if the record contradicts the earlier treatment.
- EXECUTED_UNRESOLVED: the record was not retrieved, is ACCESS_GATED, does not
  answer the predicate, or leaves a qualifier or applicability unresolved.
  Record why and keep the status; do not force PASS or FAIL.
- if the human supplies the actual record instead, evaluate it under
  HUMAN-SUPPLIED EVIDENCE; that gives the run no permission to use credentials
- a VERIFY ACTION is not a critic finding: it adds no requirement, does not
  re-decide C1-C4 and does not by itself start a second critic
- then return to G2

TARGETED ESCALATION is unchanged and stays the single pre-critic research pass.
A VERIFY ACTION is a separate, human-approved post-critic step for one exposed
or preserved blocker, not a second escalation or a general research pass. A
memo verification action (item 8) is a recommendation; it becomes a VERIFY
ACTION only under this section.

