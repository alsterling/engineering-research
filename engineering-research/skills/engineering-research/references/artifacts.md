# REFERENCE: ARTIFACTS, PROCUREMENT BOUNDARY AND RUN LOG

Production rule text, verbatim. `../SKILL.md` governs loading; its rules apply
alongside.

Also load: none.

---

# ARTIFACT CONTRACT

Canonical artifacts:
- SPEC_vN
- DISCOVERY_PACKET / DISCOVERY_LOG
- EVIDENCE_TABLE
- CHECK_RESULT_vN
- SOFT_EVIDENCE
- DECISION_MEMO
- CRITIC_BRIEF
- CRITIC_RESULT
- RUN_LOG

Each stage consumes the latest approved upstream artifact.

Do not use stale conversational state when a newer artifact exists.

Supersession:
- SPEC_v2 supersedes SPEC_v1
- CHECK_RESULT_v2 supersedes CHECK_RESULT_v1
- critic-caused HARD/lanes/qualifying-coverage change supersedes current memo
- reopened coverage requires updated DISCOVERY_PACKET, EVIDENCE_TABLE and
  CHECK_RESULT before a new memo is valid
- a changed qualifying set requires a SOFT ENRICH addendum before the replacement
  memo ranks candidates

---

# PROCUREMENT BOUNDARY

Technical qualification is not procurement readiness.

Before purchase, relevant items may include:
- exact order code
- option coexistence
- exact BOM/materials
- commercial quote
- availability
- committed lead time
- certification/calibration
- installation/application compatibility

These do not become HARD requirements unless SPEC is reopened.

---

# RUN LOG

Use `generated_templates/run-log.md` when available.

Fallback fields:
- task category
- models/tools used
- discovery route and discovery engine
- engineer hands-on time
- machine/wait time
- candidate/coverage counts
- DISCOVERY_PACKET plausible/advanced counts
- SOFT ENRICH source count and freshness
- false PASS / false FAIL / wrong configuration
- evidence conflicts/mismatches
- missed qualifying candidate found by critic
- coverage repair used/result
- checking burden
- usefulness/actionability
- workflow gap

During a run, do not propose new agents, APIs, MCPs, databases, apps, routers,
or code.

Record observed workflow gaps with evidence. "None" is valid.

Architecture changes belong outside the run.
