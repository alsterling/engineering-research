# Engineering Research

Claude Code plugin marketplace for **Engineering Research** (Public Alpha `0.6.0-alpha.1`): an
engineering selection assistant. Ask for the equipment or component you need; it understands the
problem, asks only the blocking questions, searches real products, grades manufacturer evidence,
uses an independent critic, and returns a recommendation or refuses to guess when the evidence is
insufficient. It supports engineering judgment; it does not replace it.

```bash
claude plugin marketplace add alsterling/engineering-research
```

```bash
claude plugin install engineering-research@engineering-research-marketplace
```

Then just ask, for example: "Find the best pump for this system", "Select a motor for this
mechanism", "Find a heat exchanger for this duty", "Choose a circuit breaker for these
requirements".

The Alpha may return NO RECOMMENDATION when evidence is insufficient or the top candidates remain
tied on the criteria you approved. This is intentional fail-safe behaviour.

How it works, limitations and integrity checks:
[engineering-research/README.md](engineering-research/README.md).

License: Apache License 2.0 ([LICENSE](LICENSE)).
