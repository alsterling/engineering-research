<!-- GENERATED FILE. Do not edit by hand. -->
<!-- generator: engineering-research-v0.4/packaging/scripts/generate_templates.py -->
<!-- source: engineering-research-v0.4/legacy/SKILL_v0.4_monolith.md sha256=adcc1c99f7eea100e67e1e288eaa59aff19735feb7cb76bf52991b98771dba8a -->

# TEMPLATE: EVIDENCE_TABLE row (HARD requirement)

Field names are copied verbatim, in order, from the canonical contract named
above each table. The carrier rows hold records the skill already requires,
under the names the validator reads; they add no rule. Where this template and
the skill differ, the skill governs. Never invent a value.

## For each HARD requirement, record

Canonical contract: # 4 - EXTRACT, "For each HARD requirement, record"

Carrier rows 17-19, canonical records: ## CERTIFICATION EVIDENCE AUTHORITY, "Record the authority class"; ## DOCUMENT STATES, "Record the state" and "could determine whether the predicate is satisfied".

Authority class: certification/approval sources only. Document state and
Predicate-determining: an applicable manufacturer document/record or
certification/declaration record. Leave a carrier row empty when it does not
apply.

| # | Field (canonical text) | Value |
|---|---|---|
| 1 | candidate | |
| 2 | exact MPN/configuration if known | |
| 3 | requirement ID | |
| 4 | extracted value | |
| 5 | unit | |
| 6 | operating/reference condition | |
| 7 | exact configuration vs family scope | |
| 8 | evidence grade | |
| 9 | source type | |
| 10 | source URL | |
| 11 | document title | |
| 12 | document date/revision when available | |
| 13 | page/table/section/configurator locator | |
| 14 | short supporting text/value | |
| 15 | retrieval date | |
| 16 | notes | |
| 17 | Authority class (CERTIFIER-PRIMARY, MANUFACTURER-PRIMARY or SECONDARY) | |
| 18 | Document state (RETRIEVED, NOT_IDENTIFIED, EXISTS_NOT_RETRIEVED or ACCESS_GATED) | |
| 19 | Predicate-determining (YES if the record could determine whether the predicate is satisfied, otherwise NO) | |

## Human-supplied evidence used for a HARD requirement: also record

Canonical contract: ## HUMAN-SUPPLIED EVIDENCE, "For human-supplied evidence used for a HARD requirement, record"

| # | Field (canonical text) | Value |
|---|---|---|
| 1 | original source authority/issuer | |
| 2 | original URL, registry ID, certificate/file number or equivalent locator | |
| 3 | acquisition channel: HUMAN-SUPPLIED | |
| 4 | supply date, and the retrieval date when the human states it | |
| 5 | document title | |
| 6 | revision, issue date or version when available | |
| 7 | where the document names the candidate/configuration | |
| 8 | supporting locator: page/section/table/row/registry field where practical | |
| 9 | supporting text/value used for the predicate | |
| 10 | SHA-256 of the supplied bytes when file bytes are supplied and the environment can compute it | |
