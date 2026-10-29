<!-- GENERATED FILE. Do not edit by hand. -->
<!-- generator: engineering-research-v0.4/packaging/scripts/generate_templates.py -->
<!-- source: engineering-research-v0.4/legacy/SKILL_v0.4_monolith.md sha256=adcc1c99f7eea100e67e1e288eaa59aff19735feb7cb76bf52991b98771dba8a -->

# TEMPLATE: VERIFY ACTION record

Field names are copied verbatim, in order, from the canonical contract named
above each table. This template adds no field and no rule. Where it and the
skill differ, the skill governs. Never invent a value.

## VERIFY ACTION record

Canonical contract: ## POST-CRITIC VERIFY ACTION, "VERIFY ACTION record"

| # | Field (canonical text) | Value |
|---|---|---|
| 1 | verify_action_id | |
| 2 | trigger (finding_id and/or propagation record) | |
| 3 | candidate (exact configuration) | |
| 4 | requirement_id | |
| 5 | current_status | |
| 6 | current_lane | |
| 7 | blocker | |
| 8 | verification_question | |
| 9 | target_record (the identified record/source, or "not specifically identified", which means NO_BOUNDED_VERIFY_ACTION) | |
| 10 | proposed_action (one operation) | |
| 11 | expected_resolution | |
| 12 | approval_status PROPOSED \| APPROVED \| DECLINED | |
| 13 | execution_status NOT_EXECUTED \| EXECUTED_RESOLVED \| EXECUTED_UNRESOLVED | |
| 14 | acquisition (RUN or HUMAN-SUPPLIED) | |
| 15 | evidence_refs | |
| 16 | document_state_before and document_state_after when a document is involved | |
| 17 | old_status | |
| 18 | new_status if changed | |
| 19 | result_reason | |
