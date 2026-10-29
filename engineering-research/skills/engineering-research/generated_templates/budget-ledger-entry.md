<!-- GENERATED FILE. Do not edit by hand. -->
<!-- generator: engineering-research-v0.4/packaging/scripts/generate_templates.py -->
<!-- source: engineering-research-v0.4/legacy/SKILL_v0.4_monolith.md sha256=adcc1c99f7eea100e67e1e288eaa59aff19735feb7cb76bf52991b98771dba8a -->
<!-- post-freeze projection: PF-05, PF-11, PF-19 applied in memory, projected source sha256=56bdd989b539aaa6fd86cd87c836bd751306086c34f07cbb010dbba0c0c67193 -->

# TEMPLATE: BUDGET_LEDGER entry

Field names are copied verbatim, in order, from the canonical contract named
above each table. This template adds no field and no rule. Where it and the
skill differ, the skill governs. Never invent a value.

## Pre-action BUDGET_LEDGER entry (before each countable action)

Canonical contract: # BUDGET CONTRACT, "Pre-action check and BUDGET_LEDGER"

| # | Field (canonical text) | Value |
|---|---|---|
| 1 | budget_id | |
| 2 | scope (RUN, PHASE, CANDIDATE, REQUIREMENT, VERIFY_ACTION, FALLBACK_PLAN or CRITIC_JOB) | |
| 3 | action_type | |
| 4 | limit | |
| 5 | limit_source | |
| 6 | count_before (the current count; remaining = limit - count_before) | |
| 7 | requested_increment (the next action's cost) | |
| 8 | decision ALLOW \| BLOCK_LIMIT_REACHED \| NOT_APPLICABLE | |
| 9 | count_after (count_before + requested_increment if allowed, otherwise count_before) | |
| 10 | action_ref, only for an action that executed | |
| 11 | reason | |

## Limit revision (explicit human approval only: a widening the governing rule allows, or a revision of a HUMAN or FROZEN_RUN_PLAN limit)

Canonical contract: # BUDGET CONTRACT, "record a revision"

| # | Field (canonical text) | Value |
|---|---|---|
| 1 | budget_id | |
| 2 | old_limit | |
| 3 | new_limit | |
| 4 | reason | |
| 5 | human_approval_reference | |
