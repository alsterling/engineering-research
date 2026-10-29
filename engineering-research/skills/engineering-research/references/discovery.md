# REFERENCE: DISCOVERY

Production rule text, verbatim. `../SKILL.md` governs loading; its rules apply
alongside.

Also load: none.

---

Contents:
- 3 - DISCOVERY ROUTE AND DISCOVER
  - DISCOVERY ROUTE
  - DISCOVERY_PACKET
  - DISCOVERY COVERAGE TARGET
  - ADVANCEMENT TO EXTRACT
  - VERIFICATION-SOURCE BUDGET
  - FAMILY-COVERAGE RULE

---

# 3 - DISCOVERY ROUTE AND DISCOVER

Goal:

HIGH RECALL FIRST. VERIFICATION COMES LATER.

A completed bake-off showed that a tightly coupled normal-search + verification
budget could preserve evidence quality yet miss a commercially strong qualifying
family. Deep discovery found that family while verification-oriented runs did not.
Therefore discovery and verification have separate budgets in v0.4.

## DISCOVERY ROUTE

Choose the route from the product market before naming a preferred candidate.
Do not hard-code a model vendor. Use the strongest available tool in the route.

STRUCTURED COMPONENT MARKET
- Examples: semiconductors, passives, connectors, PCB-level electronic parts.
- Prefer structured component catalogs/APIs/MCPs or parametric search first.
- Use broad/deep web research for gaps, manufacturer documents, or families not
  represented in the structured source.

OPEN INDUSTRIAL MARKET
- Examples: industrial switches, power supplies, valves, sensors, transmitters,
  drives, lab/control-panel equipment spread across many manufacturer catalogs.
- Prefer a strong deep-research/discovery mode when available.
- Use manufacturer catalogs, direct stores, industrial distributors and supplier
  search as coverage inputs.

NARROW / KNOWN MARKET
- Examples: one known family, a bounded replacement search, or a small vendor set.
- Use bounded ordinary search/fetch. Deep research is optional, not mandatory.

Record in DISCOVERY_LOG:
- route chosen
- discovery engine/tool
- why the route fits the market
- source classes covered

Discovery engine choice is a replaceable profile, not part of the engineering
truth model. Re-benchmark engines when product capabilities materially change.

## DISCOVERY_PACKET

DISCOVER produces a DISCOVERY_PACKET (it may be embedded in DISCOVERY_LOG).
For every plausible family/configuration record:
- manufacturer
- family
- exact configuration if found
- how found
- discovery-only HARD hints and apparent mismatches
- source leads (manufacturer page/datasheet/manual/certification when found)
- current commercial hints when visible (price/stock/lead time; not yet evidence)
- sibling/successor/newer/alternate checked YES/NO
- why it is or is not advanced to EXTRACT
- coverage note

Discovery claims are NOT EVIDENCE_TABLE rows and cannot create PASS, FAIL,
CONDITIONAL or CONFLICT. Search snippets are discovery leads only.

Do not assign CHECK statuses during DISCOVER.

## DISCOVERY COVERAGE TARGET

For OPEN INDUSTRIAL and broad STRUCTURED COMPONENT markets, default target:
- 12-20 plausible families when the market allows
- at least 8 manufacturers when the market allows
- include obvious low-cost/value, incumbent/common, and specialist alternatives
- log uncovered manufacturers/source classes at the boundary

For NARROW / KNOWN markets, scale this target down to the actual market.

The discovery engine's internal page/search count is not the verification budget.
If the engine reports its source/search count, record it in RUN_LOG.

## ADVANCEMENT TO EXTRACT

Advance no more than 12 candidates to full EXTRACT in the normal verification
pass. Choose the set mechanically from the DISCOVERY_PACKET:
1. no discovery-level HARD mismatch
2. exact configuration and primary document set appear retrievable
3. likely fit to the human-approved SOFT priorities
4. manufacturer/family diversity and uncovered-market coverage

SOFT hints may prioritize which plausible candidates are verified first, but they
never exclude a candidate as a HARD failure and never create a HARD status.
Reserve coverage diversity when the market is broad; do not fill all slots with
near-identical siblings merely because their pages are easy to retrieve.

## VERIFICATION-SOURCE BUDGET

The normal verification pass (EXTRACT, not broad discovery) defaults to:
- no more than 45 distinct opened source records
- no more than 3 primary manufacturer documents per advanced candidate
- no more than 10 explicit sibling/successor verification branches

A source counts when its content is opened/read or a configurator record is
materially inspected. Search snippets do not count. Count a configurator once per
candidate.

If verification limits collide:
1. preserve the required manufacturer document set for the strongest candidates
2. preserve exact-configuration evidence
3. advance fewer lower-priority candidates and log `not verified: budget`

Never thin an advanced candidate's document set merely to keep more candidates.
Budget exhaustion never relaxes SPEC.

## FAMILY-COVERAGE RULE

Before DISCOVER closes, check obvious sibling/successor/newer/alternate families
for advanced manufacturers when such branches are apparent. Record the checks.
Do not assume the first family found from a manufacturer is its best family.

---
