# REFERENCE: RETRIEVAL FALLBACK

Production rule text, verbatim. `../SKILL.md` governs loading; its rules apply
alongside.

Also load: `verify-action.md`; `evidence.md`; `certification.md` for a
RETRIEVAL FALLBACK plan; `human-supplied-evidence.md` when the human supplies
the record.

---

## RETRIEVAL FALLBACK

Why: an identified record can sit behind a dead or unindexed link; without an
ordered, bounded ladder the run either stops early or improvises a search.

A RETRIEVAL FALLBACK is a bounded, ordered attempt to retrieve the SAME record
targeted by an approved VERIFY ACTION. Propose a RETRIEVAL FALLBACK PLAN only
when all hold:
1. the VERIFY ACTION was explicitly approved and targets an identified record
2. it ended EXECUTED_UNRESOLVED for a retrieval reason: dead or broken locator,
   the tool could not fetch a public document, the official page moved, or the
   record is not exposed at its expected public path
3. candidate, requirement_id, blocker, verification_question and target_record
   stay unchanged
4. an alternate path could plausibly reach that same record
Never after ACCESS_GATED, and never because the evidence was unfavorable,
ambiguous or failed the predicate. Do not search for a better answer.

Approval: approving the VERIFY ACTION does not approve a fallback. The plan
names the stages it will use; present it and STOP. Execute only after the human
explicitly approves the plan. If declined, record FALLBACK_DECLINED and keep the
requirement status, lane and memo outcome; declining is not a FAIL. The plan is
separate from the VERIFY ACTION, whose direct-action-only rule is unchanged.

Ladder for one record, in this order, using the earliest applicable stage; each
stage at most once per plan:
- F0 DIRECT LOCATOR: the VERIFY ACTION itself; not repeated
- F1 SAME OFFICIAL SOURCE: look up the same record on the same manufacturer or
  certifier source by its exact identifier (title, file, certificate,
  declaration or registry ID, or exact model plus document type)
- F2 OTHER OFFICIAL PRIMARY SOURCE: the same record in another official primary
  system, such as a manufacturer document library, a certifier's public
  registry or an official certificate/declaration database
- F3 EXACT-ID PUBLIC LOCATOR: a public search used only to locate an official
  copy of the same record; every query is anchored to an exact identifier
- F4 SECONDARY LEAD TO PRIMARY: a distributor, cached or aggregator page used
  only as a lead to the exact primary record, identifier or official location;
  the secondary page itself is never HARD evidence (CERTIFICATION EVIDENCE
  AUTHORITY)
There are no other stages.

Identity: the ladder looks for the same record. Do not substitute another
product, sibling model, other configuration, obsolete record, different
standard, distributor claim, or a similar or family-level record with
unresolved applicability. A different document counts only as an AUTHORITATIVE
EQUIVALENT: an authority acceptable under CERTIFICATION EVIDENCE AUTHORITY and
the evidence rules, the same frozen requirement, applicability established
under EXPLICIT APPLICABILITY, current, and answering the same verification
question. A distributor "CE approved" statement is not one.

Stop at the first of these workflow results (not requirement statuses):
- FALLBACK_RETRIEVED: the record or an authoritative equivalent is retrieved
- FALLBACK_ACCESS_GATED: a stage needs login, authentication, an account,
  credentials or a session; record ACCESS_GATED under ACCESS BOUNDARY and stop;
  never try other paths around the gate (a human may supply the record under
  HUMAN-SUPPLIED EVIDENCE)
- FALLBACK_IDENTITY_DRIFT: a stage finds only a different, non-equivalent
  record; record it as a lead without substituting it; pursuing it needs a new
  human decision
- FALLBACK_EXHAUSTED: every approved stage was tried once without retrieval
- FALLBACK_DECLINED: the plan was not approved
- FALLBACK_NOT_NEEDED: other valid evidence, for example a human-supplied
  record, already answers the verification question
No recursive ladder and no automatic restart; a further attempt is a new human
decision.

After FALLBACK_RETRIEVED, inspect the record and handle it as an
EXECUTED_RESOLVED VERIFY ACTION (DOCUMENT STATES, re-evaluation, lane, memo);
retrieval alone decides nothing. Every other result keeps the requirement
status.

RETRIEVAL_FALLBACK record: fallback_id; verify_action_id; candidate;
requirement_id; blocker; target_record; verification_question; approval_status
PROPOSED | APPROVED | DECLINED; stage_attempts in order (stage, locator or
query, source/system, PRIMARY or SECONDARY role, result, document ID if found);
final_fallback_result; document_state_before and document_state_after;
retrieved_record_identity; authority_class and applicability result when
relevant; evidence_refs if retrieved; old_requirement_status;
new_requirement_status if re-evaluated; result_reason. No credentials or
session state.

---

