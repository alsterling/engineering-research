<!-- GENERATED FILE. Do not edit by hand. -->
<!-- generator: engineering-research-v0.4/packaging/scripts/generate_templates.py -->
<!-- source: engineering-research-v0.4/legacy/SKILL_v0.4_monolith.md sha256=adcc1c99f7eea100e67e1e288eaa59aff19735feb7cb76bf52991b98771dba8a -->

# TEMPLATE: RETRIEVAL_FALLBACK record

Field names are copied verbatim, in order, from the canonical contract named
above each table. This template adds no field and no rule. Where it and the
skill differ, the skill governs. Never invent a value.

## RETRIEVAL_FALLBACK record

Canonical contract: ## RETRIEVAL FALLBACK, "RETRIEVAL_FALLBACK record"

| # | Field (canonical text) | Value |
|---|---|---|
| 1 | fallback_id | |
| 2 | verify_action_id | |
| 3 | candidate | |
| 4 | requirement_id | |
| 5 | blocker | |
| 6 | target_record | |
| 7 | verification_question | |
| 8 | approval_status PROPOSED \| APPROVED \| DECLINED | |
| 9 | stage_attempts in order (stage, locator or query, source/system, PRIMARY or SECONDARY role, result, document ID if found) | |
| 10 | final_fallback_result | |
| 11 | document_state_before and document_state_after | |
| 12 | retrieved_record_identity | |
| 13 | authority_class and applicability result when relevant | |
| 14 | evidence_refs if retrieved | |
| 15 | old_requirement_status | |
| 16 | new_requirement_status if re-evaluated | |
| 17 | result_reason | |
