"""Plugin/connector discovery backends (layer A).

A backend turns whatever its discovery source returns into the RAW RESULT CONTRACT
(plugin_discovery.RAW_FIELDS). It copies only fields the source actually supplied and never fills
a gap with a guess. The normalizer (layer B, plugin_discovery.py) and the review gate (layer C,
review_gate.py) see only the raw contract, so a backend can be replaced without changing them.

V1 backend: AgentToolBackend. Python cannot call Claude's product discovery tools, so the agent
calls its catalog tool (in Claude Code / claude.ai: SearchPlugins for the plugin directory,
SearchMcpRegistry for the connector directory), saves the tool output unmodified as JSON, and this
backend maps it. There is no public directory REST API backend; a future supported API backend
would be one more Backend subclass returning the same contract.

Backends read data only. They never install, connect, enable or execute anything.
"""
from __future__ import annotations

OK, UNAVAILABLE = "OK", "SEARCH_UNAVAILABLE"


def _text(value):
    return value if isinstance(value, str) and value.strip() else None


def _drop_prefix(name):
    """Catalog component names look like '<plugin-uuid>:<component>'; keep the component part."""
    return name.split(":", 1)[1] if isinstance(name, str) and ":" in name else name


def map_claude_plugin_catalog(output) -> list[dict]:
    """SearchPlugins tool output -> raw contract (kind plugin)."""
    items = output.get("results") if isinstance(output, dict) else None
    if not isinstance(items, list):
        raise ValueError("plugin catalog output has no 'results' list")
    raw = []
    for it in items:
        if not isinstance(it, dict):
            raw.append(None)
            continue
        publisher = it.get("publisher") if isinstance(it.get("publisher"), dict) else {}
        trust = [f"{label}: {publisher[key]}" for key, label in (("tier", "publisher tier"),
                                                                ("basis", "review basis"))
                 if _text(publisher.get(key))]
        hints = [f"{c['type']}:{_drop_prefix(c['name'])}" for c in it.get("components") or []
                 if isinstance(c, dict) and _text(c.get("type")) and _text(c.get("name"))]
        install = [f"installation_preference: {it['installation_preference']}"] \
            if _text(it.get("installation_preference")) else []
        if isinstance(it.get("enabled"), bool):
            install.append(f"enabled: {str(it['enabled']).lower()}")
        upstream = it.get("upstream") if isinstance(it.get("upstream"), dict) else {}
        classification = it.get("classification") if isinstance(it.get("classification"), dict) else {}
        raw.append({k: v for k, v in {
            "kind": "plugin",
            "id": _text(it.get("id")),
            "name": _text(it.get("display_name")) or _text(it.get("name")),
            "description": _text(it.get("description")),
            "catalog": _text(it.get("marketplace_display_name")) or _text(it.get("marketplace_name")),
            "provider": _text((it.get("author") or {}).get("name")) if isinstance(it.get("author"), dict) else None,
            "capability_hints": hints or None,
            "install_availability": "; ".join(install) or None,
            "trust_signal": "; ".join(trust) or None,
            "url": _text(upstream.get("repo_url")),
            "category": _text(classification.get("subject")) or _text(classification.get("work_department")),
            "version": _text(it.get("authored_version")),
            "updated_at": _text(it.get("updated_at")),
        }.items() if v is not None})
    return raw


def map_claude_connector_directory(output) -> list[dict]:
    """SearchMcpRegistry tool output (claude.ai connector directory) -> raw contract (kind connector)."""
    items = output.get("results") if isinstance(output, dict) else output
    if not isinstance(items, list):
        raise ValueError("connector directory output is not a list of results")
    raw = []
    for it in items:
        if not isinstance(it, dict):
            raw.append(None)
            continue
        install = [f"installState: {it['installState']}"] if _text(it.get("installState")) else []
        for key in ("connected", "isAuthless"):
            if isinstance(it.get(key), bool):
                install.append(f"{key}: {str(it[key]).lower()}")
        hints = [f"tool:{t}" for t in it.get("tools") or [] if _text(t) and not t.startswith("+")]
        raw.append({k: v for k, v in {
            "kind": "connector",
            "id": _text(it.get("directoryUuid")),
            "name": _text(it.get("name")),
            "description": _text(it.get("description")),
            "catalog": "claude.ai connector directory",
            "capability_hints": hints or None,
            "install_availability": "; ".join(install) or None,
        }.items() if v is not None})
    return raw


MAPPERS = {
    "claude-plugin-catalog": map_claude_plugin_catalog,
    "claude-connector-directory": map_claude_connector_directory,
    "raw": lambda output: list(output.get("results", [])) if isinstance(output, dict) else list(output),
}


class Backend:
    """Interface: fetch(request) -> {"status": OK | SEARCH_UNAVAILABLE, "backend", "tool",
    "results": [raw contract dicts], "reason"?}. Read-only."""

    name = ""

    def fetch(self, request: dict) -> dict:
        raise NotImplementedError


class AgentToolBackend(Backend):
    """Results an agent obtained from its catalog tool, saved verbatim and mapped here."""

    name = "agent_tool"

    def __init__(self, source: str, tool_output, tool: str | None = None):
        if source not in MAPPERS:
            raise ValueError(f"unknown backend source {source!r}; known: {sorted(MAPPERS)}")
        self.source, self.tool_output, self.tool = source, tool_output, tool

    def fetch(self, request: dict) -> dict:
        base = {"backend": f"{self.name}:{self.source}", "tool": self.tool or "UNKNOWN"}
        if self.tool_output is None:
            return {**base, "status": UNAVAILABLE, "results": [],
                    "reason": "no catalog tool output supplied (tool not available or not run)"}
        if isinstance(self.tool_output, dict) and self.tool_output.get("error"):
            return {**base, "status": UNAVAILABLE, "results": [],
                    "reason": f"catalog tool reported an error: {str(self.tool_output['error'])[:200]}"}
        try:
            results = MAPPERS[self.source](self.tool_output)
        except ValueError as exc:
            return {**base, "status": UNAVAILABLE, "results": [], "reason": str(exc)}
        return {**base, "status": OK, "results": results}
