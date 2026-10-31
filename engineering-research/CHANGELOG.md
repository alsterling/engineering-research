# Changelog

## 0.6.0-alpha.1

- New entry point: `engineering-selector`. Ask for the equipment or component you need; the
  selector routes the problem and calls the other skills itself.
- New supporting skills: `problem-router`, `field-design-expert`, `capability-resolver`, and the
  read-only `capability-registry/` (GitHub and plugin/connector discovery, human-approved).
- Requirement approval (G1) keeps your own wording: an interpretation you did not state becomes a
  hard requirement only if you approve it.
- The final decision point (G2) continues the work: more research, a different candidate, a
  reopened spec, a critic pass, or a stop.
- Critic findings are classified MATERIAL / NON_MATERIAL / INSUFFICIENT_EVIDENCE; only a clean
  critic pass leads to a final recommendation. Tied candidates with missing deciding evidence end
  with NO RECOMMENDATION (intentional fail-safe).
- `engineering-research` (RUN) and `engineering-research-critic` (CRITIC) unchanged: frozen v0.5 RC3.
- New `ORCHESTRATION_SHA256SUMS` for the four new skills and the registry.

Known limitations: see README, "Known Alpha limitations".

## 0.5.0-alpha.1

- First Public Alpha: `engineering-research` (RUN) and `engineering-research-critic` (CRITIC),
  frozen Engineering Research v0.5 RC3.
