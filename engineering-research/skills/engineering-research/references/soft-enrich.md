# REFERENCE: SOFT ENRICH AND PRIORITIZATION

Production rule text, verbatim. `../SKILL.md` governs loading; its rules apply
alongside.

Also load: none.

---

# 7 - SOFT ENRICH AND PRIORITIZATION

Run SOFT ENRICH after the latest CHECK and any allowed targeted escalation.

Why: the bake-off produced technically qualified candidates but no unique winner
because current availability and price had not been verified. A separate research
mode found a materially better commercial candidate. Commercial freshness is a
different job from HARD qualification and gets its own bounded stage.

## Scope

Research only SPECIFY NOW candidates. VERIFY FIRST and EXCLUDED candidates do not
receive commercial ranking work unless the human explicitly requests it.

If EVIDENCE_TABLE already contains a fresh exact-SKU SOFT row gathered in this
run, copy/reference it into SOFT_EVIDENCE instead of re-researching it. Frozen
regression fixtures may treat their supplied SOFT rows as the run's current
commercial snapshot.

For each SOFT requirement that can change ranking, create/update SOFT_EVIDENCE:
- candidate and exact MPN/configuration
- SOFT requirement ID
- value
- quantity basis
- seller/source
- seller type: manufacturer/direct, authorized distributor, other distributor,
  marketplace/third party
- region/site and currency
- explicit stock status/count when available
- stated lead time when available
- URL
- retrieval timestamp/date
- notes/conflicts

## Source policy

For price/availability, prefer:
1. manufacturer/direct store
2. authorized distributor
3. reputable distributor
4. marketplace/third party only with an explicit caveat

Grade C or commercial third-party evidence may support a SOFT comparison. It can
never create a HARD PASS.

For technical SOFT attributes (for example redundant inputs), prefer existing
manufacturer A/B rows. Do not re-research them unless the value is unknown and the
SOFT order could actually reach that tie-breaker.

## Budget

Default:
- up to 3 commercial source records per SPECIFY NOW candidate
- up to 12 commercial source records total in the normal SOFT ENRICH pass

Stop earlier when the approved priority order already separates the candidates
with current evidence.

Stock, price and lead time are time-sensitive. Never silently reuse stale values
from an older run as current evidence. Record the timestamp/market.

Unknown SOFT evidence is unknown, not negative evidence and not equality.

## Prioritization

Hard gates first.

Then use the SOFT priority order approved at G1.

Do not invent:
- numeric weights
- confidence percentages
- supplier-quality scores
- unsupported reliability scores

Where practical:
1. remove dominated options only when the compared fields are actually known
2. apply approved priority order
3. explain mechanically why A outranks B

Keep PRODUCT DESIRABILITY separate from EVIDENCE CONFIDENCE.

A SOFT preference can never lift a VERIFY FIRST candidate above the technical
qualification gate.

---
