<!-- GENERATED FILE. Do not edit by hand. -->
<!-- generator: engineering-research-v0.4/packaging/scripts/generate_templates.py -->
<!-- source: engineering-research-v0.4/legacy/SKILL_v0.4_monolith.md sha256=adcc1c99f7eea100e67e1e288eaa59aff19735feb7cb76bf52991b98771dba8a -->

# TEMPLATE: DISCOVERY_PACKET / DISCOVERY_LOG

Field names are copied verbatim, in order, from the canonical contract named
above each table. This template adds no field and no rule. Where it and the
skill differ, the skill governs. Never invent a value.

## DISCOVERY_LOG route record

Canonical contract: ## DISCOVERY ROUTE, "Record in DISCOVERY_LOG"

| # | Field (canonical text) | Value |
|---|---|---|
| 1 | route chosen | |
| 2 | discovery engine/tool | |
| 3 | why the route fits the market | |
| 4 | source classes covered | |

## Family/configuration record (one per plausible family/configuration)

Canonical contract: ## DISCOVERY_PACKET, "For every plausible family/configuration record"

| # | Field (canonical text) | Value |
|---|---|---|
| 1 | manufacturer | |
| 2 | family | |
| 3 | exact configuration if found | |
| 4 | how found | |
| 5 | discovery-only HARD hints and apparent mismatches | |
| 6 | source leads (manufacturer page/datasheet/manual/certification when found) | |
| 7 | current commercial hints when visible (price/stock/lead time; not yet evidence) | |
| 8 | sibling/successor/newer/alternate checked YES/NO | |
| 9 | why it is or is not advanced to EXTRACT | |
| 10 | coverage note | |
