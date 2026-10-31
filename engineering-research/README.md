# Engineering Research (Public Alpha)

A Claude Code plugin that helps you select engineering equipment and components. Describe what you
need in plain words; the plugin works out what kind of problem it is, asks only the questions that
block the selection, searches for real products, grades the manufacturer evidence, and returns a
recommendation, or tells you plainly that the evidence is not good enough to recommend one.

**Status: Public Alpha (`0.6.0-alpha.1`).** Expect rough edges; behaviour and output formats may
change in later releases.

**Not a substitute for professional engineering judgment.** The plugin organises research and
evidence. It does not certify, approve or guarantee any product or design. A qualified engineer
remains responsible for checking the evidence and making the final selection.

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

## Use it

Just ask. You do not need to name a skill or know how the plugin works inside.

> Find the best pump for this system.

> Select a motor for this mechanism.

> Find a heat exchanger for this duty.

> Choose a circuit breaker for these requirements.

Add whatever you know: the duty, ratings, standards, environment, mounting, what is fixed and what
is still open. A more complete example:

> Choose a circuit breaker for these requirements: 3-pole motor protection for a 7.5 kW, 400 VAC
> pump motor, UL 489 listed, mounting on a 35 mm DIN rail.

What happens next:

1. **It understands the problem.** It decides whether this is a straight selection (the system is
   fixed), a design question (the mechanism or architecture is still open), or a mix of both.
2. **It challenges the architecture where necessary.** If the design is still open, it reviews the
   design first and shows you what the selection would rest on, before looking at any product.
3. **It asks only the important blocking questions.** Values you did not give stay UNKNOWN; nothing
   is invented, and an approximate number you mention is never silently turned into a hard limit.
4. **You approve the requirements.** It shows you the requirements it will select against and
   waits. Research starts only after you approve them.
5. **It searches actual equipment and components** and grades the manufacturer evidence for every
   requirement (pass, fail, conditional, conflict or unknown).
6. **It compares the candidates** and writes a shortlist with tradeoffs and open risks.
7. **An independent critic attacks the leading candidate** and looks for a product family the
   search may have missed. The critic runs in a separate, fresh Claude Code session: the plugin
   gives you a CRITIC_BRIEF; open a new session, paste it, and bring the CRITIC_RESULT back.
8. **It returns a recommendation, or refuses to guess** when the evidence is insufficient. You
   decide at the end: take the leader forward to verification, research more, check a different
   candidate, change the requirements, accept that none qualifies, or stop.

Every one of these stops waits for you. Silence is not approval.

Use public or synthetic information only. Do not give it confidential, export-controlled or
customer data.

## Known Alpha limitations

- **The Alpha may return NO RECOMMENDATION** when the evidence is insufficient, or when the top
  candidates remain tied on the criteria you approved and the deciding evidence (for example a
  price or a datasheet value) is not available. This is intentional fail-safe behaviour: the plugin
  does not invent a tie-breaker or guess a missing value. You can supply the missing information,
  ask for more research, or change the requirements.
- Crowded product categories may need more than one critic round before a result is final.
- Duplicate wording can appear in the list of blocking items.
- Product research uses the web search and fetch tools of your Claude Code session. Some
  manufacturer sites refuse automated access; their products then stay UNKNOWN rather than being
  guessed.
- Selection records are verbose; compressed storage is planned for a later version.
- Confidence is reported as MEDIUM at most in this package (see "Inside the plugin" below).

## Inside the plugin

You only need `engineering-selector`; it calls the other skills when they are needed. They stay
available on their own for advanced use.

| Skill | Role |
|---|---|
| `engineering-selector` | **The entry point.** Routes the request, runs the stages in order, stops at every human gate, keeps a SELECTION_STATE file and refuses out-of-order steps. |
| `problem-router` | Classifies the request: selection, design-led, hybrid, or not enough input yet. |
| `field-design-expert` | Reviews an open design before any product is chosen, and stops at a design gate. |
| `capability-resolver` | Only when the problem needs a tool or capability the plugin does not have: checks the bundled registry first, and searches GitHub or the plugin/connector catalogs only after you approve it. It never installs or connects anything. |
| `engineering-research` | Evidence-graded product research (the frozen v0.5 RC3 RUN skill). |
| `engineering-research-critic` | The independent critic, run by you in a fresh session (the frozen v0.5 RC3 CRITIC skill). |

The plugin has no agents, hooks, MCP servers or external services. It uses the tools your Claude
Code session already has: file read/write, web search/fetch, and a shell for the small
standard-library Python scripts (Python 3.10+) that keep the selection state and check each stage.
Without a shell the selector applies the same rules by hand and says the state is unverified.
Script paths written as `skills/<skill>/scripts/...` inside the skills are relative to this plugin
folder.

`capability-registry/` holds the read-only registry of known capabilities the resolver checks. GitHub
discovery needs a GitHub token in your environment; plugin/connector discovery needs your host's
catalog tools. Both are optional and run only after your approval.

The development-only checker `er-core` is not included. The selector therefore applies the critic's
outcome conservatively from the critic's own result: any finding that could change the result
reopens it, and the best confidence it reports is MEDIUM.

## Runtime integrity

`skills/engineering-research/` and `skills/engineering-research-critic/` are byte-for-byte the
qualified v0.5 RC3 runtime (38 files). The other four skills and `capability-registry/` are
byte-for-byte the Engineering Selector V1 release (17 files). To check a copy, run this in the
plugin folder:

```bash
sha256sum -c RUNTIME_SHA256SUMS ORCHESTRATION_SHA256SUMS
```

## License

Apache License 2.0. See [LICENSE](LICENSE). Changes by version: [CHANGELOG.md](CHANGELOG.md).
