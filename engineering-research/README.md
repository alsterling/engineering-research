# Engineering Research (Public Alpha)

A Claude Code plugin for engineering product research and selection. It turns a component or
equipment selection request with stated requirements into an evidence-based comparison and a
traceable shortlist, so a human can make the decision. An independent critic can then review the
leading candidate in a separate session.

**Status: Public Alpha.** The runtime is Engineering Research v0.5 RC3, unchanged from the version
that passed model qualification. Expect rough edges; behaviour and output formats may change in
later releases.

**Not a substitute for professional engineering judgment.** The plugin organises research and
evidence. It does not certify, approve or guarantee any product or design. A qualified engineer
remains responsible for checking the evidence and making the final selection.

## RUN and CRITIC

One plugin, `engineering-research`, with two skills:

| Skill | What it does |
|---|---|
| `engineering-research` (RUN) | Runs the selection workflow: drafts a requirements spec and stops for your approval (gate G1), searches for candidates, grades evidence for every requirement, records unknowns and conflicts, and writes a decision memo. When a leading candidate exists it writes a CRITIC_BRIEF and stops for the critic review, then applies the returned CRITIC_RESULT. It ends at gate G2, where you decide what happens next. |
| `engineering-research-critic` (CRITIC) | Reviews a CRITIC_BRIEF in a fresh session: Job 1 attacks the leading candidate, Job 2 checks one product family the run may have missed. Returns a CRITIC_RESULT. It never runs the selection workflow. |

The plugin has no agents, hooks, MCP servers or external services. It uses the tools your Claude
Code session already has: file read/write, and web search/fetch for discovery.

Use public or synthetic information only. Do not give it confidential, export-controlled or
customer data.

## Install

Requires Claude Code with plugin support.

```bash
claude plugin marketplace add alsterling/engineering-research
```

```bash
claude plugin install engineering-research@engineering-research-marketplace
```

Inside a Claude Code session the same steps are `/plugin marketplace add alsterling/engineering-research`
and `/plugin install engineering-research@engineering-research-marketplace`. Restart Claude Code
after installing.

To try it for one session without installing, from a clone of the repository:

```bash
claude --plugin-dir ./engineering-research
```

## Usage examples

RUN, in a normal session:

> I need a defensible shortlist of 3-pole motor protection circuit breakers for a 7.5 kW, 400 VAC
> pump motor. They must be UL 489 listed and fit a 35 mm DIN rail. Please qualify candidates
> against these specs.

> Our pressure transmitter on a test stand is obsolete. Find replacement candidates: 4-20 mA
> 2-wire, 0-10 bar gauge, IP67, 1/4 NPT male, ambient -20 to +80 C. I want evidence for every
> requirement.

The skill replies with a draft spec and waits. Approve it, or correct it, in a new message; research
starts only after that approval.

CRITIC, in a new session with no history from the run:

> I ran an engineering-research product selection in another session and it produced the
> CRITIC_BRIEF below. Please act as the independent critic and return the CRITIC_RESULT.
> (paste the CRITIC_BRIEF)

A sub-agent, fork or resumed conversation is not an independent critic session. Paste the
CRITIC_RESULT back into the RUN session to apply it.

## Runtime integrity

`skills/` is byte-for-byte the qualified v0.5 RC3 runtime (38 files). To check a copy, run this in
the plugin folder:

```bash
sha256sum -c RUNTIME_SHA256SUMS
```

## License

Apache License 2.0. See [LICENSE](LICENSE).
