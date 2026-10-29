# REFERENCE: BUDGET CONTRACT

Production rule text, verbatim. `../SKILL.md` governs loading; its rules apply
alongside.

Also load: the file that defines a limit, before applying that limit:
`discovery.md` (ADVANCEMENT TO EXTRACT, VERIFICATION-SOURCE BUDGET);
`soft-enrich.md` (SOFT ENRICH Budget); `critic.md` (C3 COVERAGE REPAIR);
`verify-action.md` (VERIFY ACTION); `retrieval-fallback.md` (RETRIEVAL
FALLBACK).

---

Contents:
- BUDGET CONTRACT

---

# BUDGET CONTRACT

Why: a run executed 5 searches against a human-approved limit of 4 and reported
the overrun afterwards. Limits are checked before an action executes.

This section creates no new limit. It makes these existing limits mechanical;
the numbers stay where they are defined:
- ADVANCEMENT TO EXTRACT: candidates advanced in the normal verification pass
- VERIFICATION-SOURCE BUDGET: opened source records; primary manufacturer
  documents per advanced candidate; sibling/successor verification branches
- SOFT ENRICH Budget: commercial source records per SPECIFY NOW candidate and in
  total
- C3 COVERAGE REPAIR: one pass; additional plausible candidates; additional
  verification source records
- TARGETED ESCALATION: one pass
- SECOND-MODEL CRITIC: one critic pass per run; one Job 2 family
- VERIFY ACTION: one direct operation per approved action
- RETRIEVAL FALLBACK: each stage at most once per plan
- any explicit limit the human sets for the run or for an approved step, for
  example a number of searches or opened pages
Where no limit exists, none is created here: the skill sets no search count, so
searches are budgeted only when the human or a frozen run plan sets a limit.

The DISCOVERY COVERAGE TARGET is a coverage objective, not an execution budget:
log and check it as coverage; it neither caps discovery at its upper value nor
permits exceeding another limit. The discovery engine's internal page/search
count stays outside the verification budget.

Effective limit: the most restrictive applicable limit, with its source
(SKILL, HUMAN or FROZEN_RUN_PLAN) recorded. A SKILL limit, including one
stated as a default ("defaults to", "Default:"), is a ceiling: it applies
unless a HUMAN or FROZEN_RUN_PLAN limit is more restrictive. A human may make
a limit narrower for the run or an approved step. A human does not widen a
skill limit, except where the governing rule allows human approval of more
work (TARGETED ESCALATION, a further critic pass). A human may explicitly
revise a HUMAN or FROZEN_RUN_PLAN limit, narrower or wider, by an instruction
that names the budget and states the new limit. Every other applicable limit
still holds: a new limit above a SKILL limit is not applied unless that
limit's governing rule allows the work; tell the human, and the old limit
stays. Never revise a limit or a frozen run plan without such an instruction,
and never infer one from "continue", "keep going", a tool approval or a change
of session, executor or stage. For each widening or revision, confirm the
explicit human approval, then record a revision: budget_id, old_limit,
new_limit, reason, human_approval_reference. A revision applies only to later
actions and keeps the same budget and count; earlier ledger entries stay
unchanged and an earlier overrun stays an overrun.

Counting:
- each executed search query or request counts 1; an executed retry or
  rephrased query is another search
- opened source records count as VERIFICATION-SOURCE BUDGET defines; re-reading
  evidence already held does not count
- each escalation pass, coverage repair pass, critic pass, Job 2 family, VERIFY
  ACTION operation and fallback stage counts 1
- an action that executed counts even if it failed, errored after submission or
  returned nothing; an action blocked before execution does not count
- if the tooling leaves unclear whether an action executed, record
  COUNT_AMBIGUOUS and count it for the next check; do not invent precision
- one action is never split or relabelled to avoid a count

Pre-action check and BUDGET_LEDGER: before each countable action, record
budget_id; scope (RUN, PHASE, CANDIDATE, REQUIREMENT, VERIFY_ACTION,
FALLBACK_PLAN or CRITIC_JOB); action_type; limit; limit_source; count_before
(the current count; remaining = limit - count_before); requested_increment (the
next action's cost); decision ALLOW | BLOCK_LIMIT_REACHED | NOT_APPLICABLE;
count_after (count_before + requested_increment if allowed, otherwise
count_before); action_ref, only for an action that executed; reason. If
count_before + requested_increment > limit, the decision is BLOCK_LIMIT_REACHED
and the action does not execute. Never execute first and report the overrun
afterwards.

At BUDGET_LIMIT_REACHED, record the budget, count, limit, blocked action and any
unresolved blocker, then continue under the existing rules (for example the
VERIFICATION-SOURCE BUDGET collision order, "not retrieved/read within budget"
under DOCUMENT STATES, or the escalation STOP). Do not reset or rename a
counter, open a new phase to get a fresh budget, split or relabel an action, or
pass it to another agent, model, browser, tool or session. If more work is
needed and the governing rule allows human approval, STOP and ask for it.

Budgets belong to the engineering research run and its scopes, not to an
executor: switching model, agent, subagent, browser, tool or session never
resets a count. A VERIFY ACTION and its RETRIEVAL FALLBACK plan keep their own
scopes, and a human limit set for the step covers both; moving from the action
to the fallback resets nothing.

ALLOW, BLOCK_LIMIT_REACHED, NOT_APPLICABLE, BUDGET_LIMIT_REACHED and
COUNT_AMBIGUOUS are workflow tokens, not requirement statuses.

---

