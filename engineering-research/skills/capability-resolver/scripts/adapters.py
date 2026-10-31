"""Search adapters for the Capability Resolver.

An adapter turns a list of required capability tags into candidate entries in the registry-entry
shape (id, name, type, status, install, capabilities, ...), each tagged with "adapter": <name>.
The resolver core only sees candidates, so a new discovery source is a new adapter class here,
not a change to the decision model.

The local registry adapter is the only one the resolver calls. External adapters (P3, Ecosystem
Scout: github_adapter.GitHubSearchAdapter, plugin_discovery.PluginConnectorDiscoveryAdapter) only
discover: they return UNREVIEWED candidates. A human or agent reviews every candidate, and
review_gate.to_resolver_evidence() turns the reviewed discovery into the search_record and
evaluated_options for the resolver; resolve() refuses an external adapter outright. Until an adapter
exists for a source, that search is done by hand and recorded the same way. No adapter may
install, connect, clone or execute anything.
"""
from __future__ import annotations

# P3: external discovery adapters. Implemented: github_search (github_adapter.py) and
# plugin_connector_discovery (plugin_discovery.py, agent-side backend in plugin_backends.py). The
# rest are names reserved for later adapters. Discovery output reaches the resolver only through
# review_gate.py, once every candidate is reviewed.
IMPLEMENTED_EXTERNAL_ADAPTERS = ("github_search", "plugin_connector_discovery")
PLANNED_ADAPTERS = (
    "claude_skill_discovery",
    "mcp_discovery",
    "api_tool_discovery",
)


class SearchAdapter:
    """Interface: search(required) -> candidates. Read-only; never installs or connects."""

    name = ""
    external = True

    def search(self, required: list[str]) -> list[dict]:
        raise NotImplementedError


class LocalRegistryAdapter(SearchAdapter):
    """Exact tag match against the local capability registry. Deprecated entries are skipped."""

    name = "local_registry"
    external = False

    def __init__(self, registry: dict):
        self.registry = registry

    def search(self, required: list[str]) -> list[dict]:
        wanted = set(required)
        found = []
        for entry in self.registry["entries"]:
            if entry["status"] == "deprecated" or not wanted & set(entry["capabilities"]):
                continue
            found.append({**entry, "adapter": self.name})
        return found
