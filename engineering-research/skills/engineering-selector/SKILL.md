---
name: engineering-selector
description: The single entry point for engineering selection problems. Use whenever the user wants to find, choose, select, size, specify or replace an engineering component or piece of equipment for a system ("find the best pump for this electrolyzer", "select a breaker for this machine", "what motor should I use for this mechanism", "find a heat exchanger for this duty"), whether or not the system design is settled. It routes the problem, runs design review first when the design is open, checks known capabilities before any capability discovery, runs evidence-graded selection and the independent critic, and stops at every human gate. The user does not need to know which internal skill to call. Public/synthetic T0 information only.
---

# Engineering Selector V1

One entry point. You coordinate existing skills; you do not replace them and you do not do their
work yourself. Each skill keeps its own rules, gates and STOPs.

| Stage | Skill | Ends with |
|---|---|---|
| route | `problem-router` | PROBLEM_ROUTE |
| design review | `field-design-expert` | FIELD_DESIGN_RESULT + draft ENGINEERING_RESEARCH_HANDOFF |
| capability gap (only if one exists) | `capability-resolver` | CAPABILITY_DECISION |
| selection | `engineering-research` (RUN) | G1 stop, CRITIC_BRIEF stop, G2 stop |
| independent critic | `engineering-research-critic`, in a FRESH session run by the human | CRITIC_RESULT |

## Flow

```
SELECTION_LED      -> RUN (G1) -> RUN research -> critic -> RUN applies critic -> G2 result
DESIGN_LED, HYBRID -> Field/Design Expert -> [Capability Resolver, only for a real gap]
                      -> DESIGN GATE (human) -> RUN (G1) -> ... -> critic -> G2 result
INSUFFICIENT_INPUT -> ask only the blocking questions -> wait -> route again with the answers

G2 (human decides; G2 is not the end):
  ADDITIONAL_RESEARCH, VERIFY_DIFFERENT_CANDIDATE -> back to the RUN (SPEC, G1 and evidence kept) -> ...
  REOPEN_SPEC              -> back to G1 (explicit APPROVE_SPEC again before any research)
  ADVANCE_TO_VERIFICATION  -> leader with a clean critic pass (label 4, or label 3 with every finding
                              NON_MATERIAL) and no open critic finding: FINAL result
                              leader without one: RUN writes the CRITIC_BRIEF -> fresh-session critic -> G2
                              open findings the RUN must address: refused (research or reopen first)
  ACCEPT_NONE, STOP        -> FINAL, no recommendation
```

## Rules

1. **Route first.** Invoke `problem-router` on the user's words. Do not search, name or rank
   products before the RUN stage, and in the RUN stage only after G1 approval. Never research a
   product yourself (no web search or fetch, no catalog lookup, no product names from memory)
   outside the `engineering-research` skill; its evidence is the only product evidence.
2. **Selection-led stays fast.** Do not call `field-design-expert` for a SELECTION_LED route. Hand
   the user's request to `engineering-research` unchanged.
3. **Design-led and hybrid do design first.** Call `field-design-expert`, then stop at the design
   gate. No `engineering-research` call until the human approves the handoff at that gate.
4. **Capabilities: known first.** The pipeline above is the known capability set. Call
   `capability-resolver` only for an entry in the expert's `capability_needs` that `selector.py`
   reports as a gap (no usable registry entry covers its tag). A missing value (head, pressure,
   duty, travel, a measurement) is an information gap: it goes to the design gate, never to the
   resolver. Run the resolver's local script only; external discovery (GitHub, plugin or connector
   catalogs) needs the human's APPROVE_DISCOVERY at the design gate, and its candidates go through
   the resolver's review gate. Never install, enable, connect, clone or build anything: the human
   does that, after approving it.
5. **Human gates are real.** CLARIFY, DESIGN GATE, G1, CRITIC and G2 each STOP and wait for the
   human, also in unattended runs. Silence is not approval. Do not answer a gate yourself, do not
   assume an answer, and do not continue past a gate in the same turn.
6. **Ask only what blocks.** At CLARIFY ask only the router's blocking questions. At the design
   gate, list the unknowns that the selection would rest on (first-order variables and
   requirements still UNKNOWN) and say what resolves each. Never fill a value the user did not
   give; never turn a reference, approximate or screening number into a HARD limit.
7. **Respect scope.** Anything the user puts out of scope stays out: never a requirement, a
   reference value or an in-scope search item. Say it under out of scope.
8. **G1 approves only what the human said or approved.** At the RUN's G1 stop, `selector.py`
   classifies every draft-SPEC row: USER_STATED (value and operator are in the user's words),
   USER_APPROVED (an earlier explicit human approval), PROPOSED_ENGINEERING_CONSTRAINT (an
   interpretation the user did not state, for example "400 VAC" read as "rated voltage >= 400 VAC"),
   or UNKNOWN. Show the human that table with the RUN's G1 content. A proposed constraint becomes
   HARD only if the human writes APPROVE for it; an UNKNOWN stays UNKNOWN unless the human supplies
   it. A REJECT sends the SPEC back to the RUN for a redraft. After G1, a HARD row that differs from
   the approved one is refused: change it only through a reopened SPEC.
9. **Critic before any final answer.** If the RUN memo names a preferred candidate, the
   CRITIC_BRIEF goes to `engineering-research-critic` in a fresh session that the human starts (do
   not run the critic yourself, in a sub-agent or a fork). The CRITIC_RESULT goes back to the RUN
   skill, which applies it. A critic that disqualified the leader, changed a HARD state or found a
   missed qualifying family (labels 1-3), or an invalid critic result, is never presented as a
   final answer until the RUN has applied it; say plainly that the critic changed the result.
   The result is FINAL only after the human chooses ADVANCE_TO_VERIFICATION for a leader whose
   critic pass is clean (label 4, or label 3 with every finding NON_MATERIAL, applied by the RUN)
   while no critic finding is open, or ends at G2 with ACCEPT_NONE or STOP (no recommendation).
   Until then show it as PROVISIONAL.
9a. **Critic materiality (never ignore a label).** `selector.py` classifies every critic finding at
   each G2 stop: MATERIAL (could change the leader, a HARD state, the approved ranking, a safety or
   reliability conclusion, or the evidence confidence), NON_MATERIAL (a missed candidate that also
   passes every HARD requirement on manufacturer evidence and is dominated by the leader on the
   G1-approved ranking, with comparable SOFT evidence for both), or INSUFFICIENT_EVIDENCE. A HARD,
   safety, interpretation or provenance finding is never NON_MATERIAL. MATERIAL and
   INSUFFICIENT_EVIDENCE block the final result; NON_MATERIAL is recorded and needs no research loop.
   Show the G2 gate's `critic_findings` (class and reasons) to the human. Do not decide materiality
   yourself and do not invent a tie-breaker: an UNKNOWN value on a deciding criterion stays UNKNOWN.
10. **G2 continues the work.** After ADDITIONAL_RESEARCH, VERIFY_DIFFERENT_CANDIDATE, REOPEN_SPEC or an
   ADVANCE_TO_VERIFICATION without a critic PASS, run `request` and hand its text to the
   `engineering-research` skill in the same RUN session: it continues from its latest artifacts. A
   continued round records a newer CHECK_RESULT version; the superseded round stays in the state.
11. **Do not modify** any of the skills you call, and do not paraphrase their rules into new ones.

## State and checks

If a shell is available, keep the state with `scripts/selector.py` in this skill's directory
(call it `SELECTOR` below). It refuses any step out of order and leaves the state unchanged.

```
python SELECTOR init   --state SELECTION_STATE.json --statement STATEMENT.txt
python SELECTOR record --state SELECTION_STATE.json --artifact ARTIFACT.json
python SELECTOR answer --state SELECTION_STATE.json --answer ANSWER.json
python SELECTOR status --state SELECTION_STATE.json      # ENGINEERING_SELECTION_STATUS
python SELECTOR request --state SELECTION_STATE.json     # the request to hand to the RUN skill
python SELECTOR result --state SELECTION_STATE.json      # ENGINEERING_SELECTION_RESULT at G2
```

Save the user's request verbatim as STATEMENT.txt. What to record, after each stage:
- the PROBLEM_ROUTE JSON as it is;
- `{"artifact": "FIELD_DESIGN", "result": FIELD_DESIGN_RESULT, "handoff": ENGINEERING_RESEARCH_HANDOFF}`;
- `{"artifact": "CAPABILITY_RESOLUTION", "request": REQUEST, "decision": RESOLVER_JSON_OUTPUT}`,
  one per gap (from `resolver.py --request REQUEST.json --json`);
- `{"artifact": "RUN_STOP", "stop": "G1 | CRITIC_HANDOFF | G2", "run_session_id": "...", "spec": SPEC,
  "check_result": CHECK_RESULT, "memo": {"preferred": "candidate_id or null", "shortlist": [...],
  "tradeoffs": [...], "unresolved_risks": [...], "next_action": "...", "critic_applied": false}}`
  with the RUN skill's canonical SPEC and CHECK_RESULT (a G1 stop carries the SPEC only; the SPEC keeps
  each row's `class` and its `soft_priority_order`, as the RUN wrote them);
  CHECK_RESULT in JSON carries at least `{"version": N, "candidates": [{"candidate_id": "...", "name":
  "...", "lane": "SPECIFY NOW | VERIFY FIRST | EXCLUDED", "cells": {"R1": {"status": "PASS | FAIL |
  CONDITIONAL | CONFLICT | UNKNOWN"}}}]}`, transcribed from the RUN's CHECK_RESULT_vN;
- the CRITIC_RESULT the human brings back, transcribed to JSON with the field names of the critic's
  CRITIC_RESULT CONTRACT: `artifact_type` "CRITIC_RESULT", `critic_session_id`, `critic_model`,
  `critic_family`, `consumed_check_result_version`, `job1` {`leader`, `findings` or
  `no_hard_status_change`}, `job2`, `C1`..`C4` "YES | NO" with `C1_basis`..`C4_basis`,
  `advisory_outcome_label` {`number`, `text`}, `evidence`, and `independence` {`primary_model`,
  `primary_session_id`, `critic_model`, `critic_session_id`, `session_independence`, `critic_family`,
  `context_independence`, `independence_quality`, `independence_reason`}. Transcribe; never change a
  finding, a status or the label. Include `job2.rows` ({requirement id: {status, evidence_refs}}) and
  every `evidence` row with its `authority`;
- at the G2 stop after a critic, the memo also carries, from the RUN's applied result: `soft_values`
  `{candidate_id: {"S1": {"value": 30, "unit": "mm", "source": "MANUFACTURER datasheet, D4 p.1"}, ...}}`
  for the leader and every candidate a critic named, one entry per SOFT ranking criterion (`{"value":
  "UNKNOWN"}` where the RUN has no value; `source` MANUFACTURER, DERIVED, or DISTRIBUTOR for a price);
  `critic_candidate_ids` `{"<critic exact candidate>": "<candidate_id>"}` when the names differ; and
  `critic_concerns` `[{"type": "SAFETY | RELIABILITY | HARD | REQUIREMENT_INTERPRETATION |
  MANUFACTURER_CLAIM | PROVENANCE | EVIDENCE_QUALITY", "text": "...", "critic_disposition": "OPEN |
  CLOSED_BY_CRITIC", "quote": "<the critic's own words>", "candidate": "<candidate_id> | null",
  "requirement_ids": ["R3"] | []}]` for every such concern or caveat the CRITIC_RESULT raises (an empty
  list if none). `CLOSED_BY_CRITIC` only where the critic itself says it changes nothing (for example
  "not a CONFLICT", "PASS stands"), quoted; otherwise `OPEN`. `candidate` is the candidate the concern
  is about (null, with `requirement_ids` [], only for a process-level note such as a same-family critic
  or the bounded Job 2 scope); `requirement_ids` are the HARD requirements it could affect. An open
  concern about the leader, or about a candidate that could outrank it, blocks the final result; a
  closed caveat or a process-level note is recorded and shown under unresolved risks; a SAFETY or
  RELIABILITY concern is always treated as open.

Record a human answer only from the human's own words:
`{"gate": "<open gate id>", "decision": "...", "text": "...", "acknowledged_unknowns": [...] | "ALL",
"capabilities": {"<gap tag>": "APPROVED | DEFERRED"}, "tags": [...]}` (only the fields the decision
needs). Decisions: CLARIFY `ANSWER`; DESIGN GATE `APPROVE_HANDOFF`, `SUPPLY_INFORMATION`,
`APPROVE_DISCOVERY`; G1 `APPROVE_SPEC` with `"requirement_decisions": {"<row id>": "APPROVE | REJECT"}`
for every row the gate lists under `decisions_needed` and `"acknowledged_unknowns": [<every row id
under unknowns>] | "ALL"`, or `CHANGE_SPEC`; CRITIC `SKIP_CRITIC`; G2
`ADVANCE_TO_VERIFICATION`, `ADDITIONAL_RESEARCH` (text: what to research), `VERIFY_DIFFERENT_CANDIDATE`
(`"candidates": [...]` and/or text), `REOPEN_SPEC` (text: the change), `ACCEPT_NONE`; any gate `STOP`.
The G2 decision must be one of these names: map the human's words to the option they chose, and ask if
they named none. After `SUPPLY_INFORMATION` or `ANSWER`, rerun the stage the selector names (the
expert, or the router) on the updated statement.

A REFUSED line means the step is out of order or an artifact fails its skill's check: fix it, or
tell the human what is blocking. Never edit the state file by hand. If no shell is available,
apply the same rules by hand and say the state is unverified.

**Resume.** On a later turn or in a new session, read SELECTION_STATE.json, run `status`, and
continue from the stage it names. The human's answer resumes the stopped gate.

## What the user sees

End every stop with this status block: paste the `status` output as it is printed, starting with
the line `ENGINEERING_SELECTION_STATUS` (do not rename it or rewrite it as a prose "Status"
section). This holds also when a called skill has just presented its own gate (for example the RUN
skill's G1): give that skill's gate content, then the status block, so the user always sees where
the selection stands.

```
ENGINEERING_SELECTION_STATUS
- problem type: (route, in one plain sentence)
- known: (what the user stated, with its qualifiers)
- out of scope: (if the user excluded anything)
- blocking selection: (unknowns, open gaps or questions)
- stage: (where the system is, and what is done)
- needed from you: (the exact decision or information requested)
```

At G2, show the result (from `result`):

```
ENGINEERING_SELECTION_RESULT
- status: (PROVISIONAL at G2; FINAL after a critic PASS or an explicit stop)
- recommended: (candidates and lanes from the RUN, after the critic)
- requirements:
- evidence summary:
- tradeoffs:
- unresolved risks:
- critic: (label, and whether it changed the result)
- confidence / evidence quality:
- next engineering action:
```

Show artifacts in JSON only if the user asks for them. Public/synthetic information only (T0).
