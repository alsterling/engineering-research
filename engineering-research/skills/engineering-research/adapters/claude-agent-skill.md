# ADAPTER: CLAUDE / AGENT SKILL RUNTIME

Runtime adapter for the `engineering-research` skill when it runs as an Agent Skill in a Claude
runtime that can read the skill directory with a file-read or shell tool (for
example Claude Code or the Claude Agent SDK). It maps mechanics only. Every
rule, gate, limit and token keeps the meaning given in `../SKILL.md` and its
references; where this adapter and the skill seem to differ, the skill governs.

Agent Skill levels:
- Level 1: the frontmatter `name` and `description` are what the runtime reads
  to decide whether the skill applies.
- Level 2: `../SKILL.md` body is loaded when the skill is used.
- Level 3: files under `references/` are read on demand under REFERENCE
  LOADING. The runtime does not load them by itself.

| Operation | Skill requirement (where) | Claude / Agent Skill mechanics |
|---|---|---|
| load reference | REFERENCE LOADING | Read the file with the file-read tool (or `cat` through the shell tool) at its path relative to the skill directory. Read the whole file: no offset or line limit that cuts it short. A search hit inside the file is not a load. |
| stop | every STOP; MODES ("Every STOP holds in unattended and agent modes") | End the assistant turn and wait for the next user message. Do not continue past a STOP through scheduled tasks, wake-ups, loops, background jobs, hooks or sub-agents. |
| human approval | HUMAN GATE G1, HUMAN GATE G2, TARGETED ESCALATION, a further critic pass, VERIFY ACTION, RETRIEVAL FALLBACK plan, budget revisions | A user message that names the gate, action or plan it approves. A tool-permission prompt the user accepts approves that tool call only; it is not approval of a gate, a VERIFY ACTION or a RETRIEVAL FALLBACK plan. A permission mode that auto-accepts tool calls is not approval either. |
| fresh critic session | RUN MODE - CRITIC HANDOFF; CRITIC INDEPENDENCE | The human opens a new conversation or session that has no history from the primary run, no project memory or files from it beyond the CRITIC_BRIEF, and gives it the CRITIC_BRIEF. A sub-agent (Task / Agent tool), a forked or resumed conversation, or any session the primary run starts is not this handoff. |
| session and model identity | CRITIC INDEPENDENCE record | Record the model ID the runtime reports and the provider, and the session ID when the runtime exposes one. Record "not available" otherwise. Classification under CRITIC INDEPENDENCE is made from these records, not by this adapter. |
| external research mode | Research-mode timing; DISCOVERY ROUTE | Where a research or deep-research mode is a setting the user turns on, the user turns it on only after G1 approval. Where web search and fetch tools are the discovery engine, record them as the engine in DISCOVERY_LOG. |
| search and fetch | ACCESS BOUNDARY; DISCOVERY ROUTE; # 4 - EXTRACT | Web search tool calls find leads; web fetch tool calls and connector document reads open source records. What counts, and how, is defined by VERIFICATION-SOURCE BUDGET and BUDGET CONTRACT. |
| authenticated sessions | ACCESS BOUNDARY | Browser tools that operate the user's own browser act inside the user's logged-in sessions. Do not use them to retrieve evidence. Use web fetch tools, or a browser that holds no login, cookie or saved credential. |
| action count | BUDGET CONTRACT | Take counts from the tool-use transcript. It shows what executed; it is not the unit of count. Count only the units BUDGET CONTRACT defines, never one unit per tool call. One call can hold several countable units: a batched call that runs two queries is two searches, and a call that opens three distinct source records is three opened source records. One call can hold no new unit for a budget: re-reading a record already held opens no new source record. Batching never lowers a count. Tool calls made by sub-agents or other sessions of the same run are part of the same count. If the transcript cannot show whether an action executed, apply that contract's rule for an unclear count. |
| file read/write | ARTIFACT CONTRACT; HUMAN-SUPPLIED EVIDENCE | Write artifacts with the file-write tool, one Markdown file per artifact version. Compute the SHA-256 of supplied bytes with `sha256sum` or Python `hashlib` when a shell is available. |
| templates | MODES (Templates) | `generated_templates/` relative to `../SKILL.md`. A skill directory packaged without that directory has no templates: use the fallback fields in the skill. |
| unattended execution | MODES; every STOP | A headless, SDK or CI run executes up to the first STOP, writes what the gate presents, and ends. Only a new user message resumes the run. |
