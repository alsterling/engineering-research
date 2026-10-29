# ADAPTER: GENERIC FILESYSTEM / TOOL-CAPABLE AGENT

Runtime adapter for the `engineering-research` skill. It maps the skill's abstract operations to the
mechanics of a generic agent that reads and writes files and calls tools
(search, fetch, shell). It maps mechanics only. Every rule, gate, limit and
token keeps the meaning given in `../SKILL.md` and its references; where this
adapter and the skill seem to differ, the skill governs.

Use this adapter only when the runtime can do all of the following:
- read a named file from the package directory in full
- write artifact files
- end its turn and wait for a human message before doing anything more
- let a human start a separate agent conversation or process that receives only
  the files the human gives it

A runtime that cannot pause for a human message cannot run this skill: every
STOP must be a real pause.

| Operation | Skill requirement (where) | Generic mechanics |
|---|---|---|
| load reference | REFERENCE LOADING | Open the reference with the file-read tool, at its path relative to `../SKILL.md`, and read it to the end before the step it governs. A chunk, a search hit inside the file or a summary of it is not a load. If the read fails, the REFERENCE LOADING STOP applies. |
| stop | every STOP; MODES ("Every STOP holds in unattended and agent modes") | End the turn with the material the gate presents. Make no further tool call and schedule no continuation. Resume only on a new human message. |
| human approval | HUMAN GATE G1, HUMAN GATE G2, TARGETED ESCALATION, a further critic pass, VERIFY ACTION, RETRIEVAL FALLBACK plan, budget revisions | A human message that names the gate, action or plan it approves. These are not approval: silence, a timeout, a default, a configuration flag, a tool-permission or sandbox prompt, an approval given for a different step, and any message written by an agent or tool. |
| fresh critic session | RUN MODE - CRITIC HANDOFF; CRITIC INDEPENDENCE | The human starts a new agent conversation or process with no history, memory or shared context from the primary run and gives it only the CRITIC_BRIEF and the material the brief includes or references. A sub-agent, thread, role-play or tool call started by the primary run is not this handoff. |
| session and model identity | CRITIC INDEPENDENCE record | Record the identifiers the runtime exposes: model name and version, provider, conversation, process or session ID. Record "not available" for any identifier it does not expose; never invent one. Classification under CRITIC INDEPENDENCE is made from these records, not by this adapter. |
| external research mode | Research-mode timing; DISCOVERY ROUTE | A research agent, deep-research service or bulk-search tool used for discovery is the discovery engine. Start it only after G1 approval. Record which engine was used in DISCOVERY_LOG. |
| search and fetch | ACCESS BOUNDARY; DISCOVERY ROUTE; # 4 - EXTRACT | Search tools find leads; fetch or file-download tools open source records. What counts, and how, is defined by VERIFICATION-SOURCE BUDGET and BUDGET CONTRACT. |
| authenticated sessions | ACCESS BOUNDARY | Retrieve evidence only with fetch tools or browser profiles that hold no logged-in session, stored cookie or saved credential. If the only available browser carries a human's login, do not use it to retrieve evidence. |
| action count | BUDGET CONTRACT | Take counts from the runtime's tool-call log. It shows what executed; it is not the unit of count. Count only the units BUDGET CONTRACT defines, never one unit per tool call. One call can hold several countable units: a batched call that runs two queries is two searches, and a call that opens three distinct source records is three opened source records. One call can hold no new unit for a budget: re-reading a record already held opens no new source record. Batching never lowers a count. If the log cannot show whether an action executed, apply that contract's rule for an unclear count. Calls made by any helper process of the run are part of the same log. |
| file read/write | ARTIFACT CONTRACT; HUMAN-SUPPLIED EVIDENCE | Keep each canonical artifact as its own Markdown file; a new version is a new file with the new version name. Compute the SHA-256 of supplied bytes with a local hash tool when one is available. |
| templates | MODES (Templates) | `generated_templates/` relative to `../SKILL.md`. If that directory is not present, use the fallback fields in the skill. |
| unattended execution | MODES; every STOP | A scheduled, headless or batch run executes up to the first STOP, writes what the gate presents, and ends. It never approves its own gate and never passes a gate to another agent for approval. |
