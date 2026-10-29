<!-- GENERATED FILE. Do not edit by hand. -->
<!-- generator: engineering-research-v0.4/packaging/scripts/generate_templates.py -->
<!-- source: engineering-research-v0.4/legacy/SKILL_v0.4_monolith.md sha256=adcc1c99f7eea100e67e1e288eaa59aff19735feb7cb76bf52991b98771dba8a -->
<!-- post-freeze projection: PF-05, PF-11, PF-19 applied in memory, projected source sha256=56bdd989b539aaa6fd86cd87c836bd751306086c34f07cbb010dbba0c0c67193 -->

# TEMPLATE: CRITIC_RESULT

Field names are copied verbatim, in order, from the canonical contract named
above each table. This template adds no field and no rule. Where it and the
skill differ, the skill governs. Never invent a value.

## Run identity

Canonical contract: ## CRITIC_RESULT CONTRACT, Run identity

| # | Field (canonical text) | Value |
|---|---|---|
| 1 | run_id | |
| 2 | critic_session_id, or "not available" | |
| 3 | critic model / platform / mode, as reported | |
| 4 | critic_family: SAME \| CROSS \| UNKNOWN, relative to the primary run, with the other CRITIC INDEPENDENCE fields | |

## JOB 1 - attack the leader

Canonical contract: ## CRITIC_RESULT CONTRACT, JOB 1

| # | Field (canonical text) | Value |
|---|---|---|
| 1 | leader candidate and exact configuration | |
| 2 | either one block per finding, or JOB1_NO_HARD_STATUS_CHANGE with the documents/evidence examined | |
| 3 | each finding: finding_id (stable, for example J1-F1), requirement_id (in the frozen SPEC), old_status, new_status, finding_type (EVIDENCE \| RULE_ONLY \| SEMANTIC_INTERPRETATION), rule_applied, evidence_refs (required for both types; CRITIC FINDING TYPES), reason | |

## JOB 2 - one missed-family check

Canonical contract: ## CRITIC_RESULT CONTRACT, JOB 2

| # | Field (canonical text) | Value |
|---|---|---|
| 1 | family examined, and the exact candidate/configuration or "not resolved" | |
| 2 | why this family was chosen | |
| 3 | eligibility_class (UNCOVERED \| LOGGED_UNSCREENED) and eligibility_basis, under JOB 2 ELIGIBILITY | |
| 4 | HARD requirement IDs in the order checked, with evidence_refs | |
| 5 | result: JOB2_HARD_FAIL \| JOB2_NO_HARD_FAIL \| JOB2_NOT_COMPLETED (with its reason, for example ELIGIBILITY_NOT_ESTABLISHED) | |
| 6 | JOB2_HARD_FAIL: first failing requirement_id, required predicate, actual evidence-supported value/state, evidence_ref, stop point | |
| 7 | JOB2_NO_HARD_FAIL: requirement_id, status and evidence_refs for every frozen HARD requirement | |

## Enforcement fields, all four present

Canonical contract: ## CRITIC_RESULT CONTRACT, Enforcement fields

| # | Field (canonical text) | Value |
|---|---|---|
| 1 | C1: YES \| NO, C1_basis: finding IDs or NONE | |
| 2 | C2: YES \| NO, C2_basis: finding IDs or lane-transition reference, or NONE | |
| 3 | C3: YES \| NO, C3_basis: Job 2 candidate and evidence-completeness reference, or NONE | |
| 4 | C4: YES \| NO, C4_basis: explicit basis or NONE | |
| 5 | advisory_outcome_label: exactly one of labels 1-4 below, number and text, consistent with the reported C1-C4 | |

## Evidence references

Canonical contract: ## CRITIC_RESULT CONTRACT, Evidence references

| # | Field (canonical text) | Value |
|---|---|---|
| 1 | evidence_refs point by stable ID (for example D1) to evidence rows in the CRITIC_RESULT's own evidence section; each row carries the HARD PASS TRACEABILITY fields and states whether the primary run already had it | |
| 2 | never an unnamed source, "manufacturer data", an untraceable search result or an unsupported prose assertion | |

## Independence record

Canonical contract: ## CRITIC INDEPENDENCE, "Record with the CRITIC_RESULT"

| # | Field (canonical text) | Value |
|---|---|---|
| 1 | primary_model | |
| 2 | primary_model_family when known | |
| 3 | primary_session_id or "not available" | |
| 4 | critic_model | |
| 5 | critic_model_family when known | |
| 6 | critic_session_id or "not available" | |
| 7 | session_independence | |
| 8 | critic_family | |
| 9 | context_independence | |
| 10 | independence_quality | |
| 11 | independence_reason | |
