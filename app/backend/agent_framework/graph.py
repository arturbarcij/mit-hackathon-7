"""Audit DAG for the Jani orchestrator.

Every seat is an audit. Builder seats report gaps. They do not edit owned
product paths. This graph does not generate the product.

An agent starts only after every seat it depends on has finished.
Independent seats may run at the same time.

Edges, in words:

- research before content and docs
- ml before engine
- content and engine before ui
- research, ml, engine, ui, content, and docs before qa
- qa before redteam and judge

The direct edges into qa are deliberate. If a middle seat is filtered out,
qa still waits for each remaining builder.

An edge is kept only when both ends are in the selected set. A seat must
not wait for a seat that is not running, and an edge that points at a seat
outside the selection is dropped.
"""

from __future__ import annotations

from typing import Iterable

from .roster import AgentSpec

# (upstream, downstream). Downstream starts after upstream has finished.
EDGES: tuple[tuple[str, str], ...] = (
    # research before content and docs
    ("research", "content"),
    ("research", "docs"),
    # ml before engine
    ("ml", "engine"),
    # content and engine before ui
    ("content", "ui"),
    ("engine", "ui"),
    # all of those builders before qa
    ("research", "qa"),
    ("ml", "qa"),
    ("engine", "qa"),
    ("ui", "qa"),
    ("content", "qa"),
    ("docs", "qa"),
    # qa before redteam and judge
    ("qa", "redteam"),
    ("qa", "judge"),
)

EDGES_DOC = (
    "research before content and docs; "
    "ml before engine; "
    "content and engine before ui; "
    "research, ml, engine, ui, content, and docs before qa; "
    "qa before redteam and judge. "
    "An edge is kept only when both seats are selected."
)


def edges_for(selected: Iterable[str]) -> list[tuple[str, str]]:
    """Return EDGES whose upstream and downstream are both selected."""
    chosen = {item.strip() for item in selected if item and item.strip()}
    return [(src, dst) for src, dst in EDGES if src in chosen and dst in chosen]


def predecessors(selected: Iterable[str]) -> dict[str, list[str]]:
    """Upstream ids for each selected seat, in EDGES order."""
    chosen = [item.strip() for item in selected if item and item.strip()]
    deps = {agent_id: [] for agent_id in chosen}
    for src, dst in edges_for(chosen):
        deps[dst].append(src)
    return deps


def build_plan(
    specs: list[AgentSpec],
    edges: list[tuple[str, str]],
    state: dict[str, str],
    *,
    claude: str,
    block_reason: str | None = None,
) -> dict:
    """Plan document: nodes, edges, and state. Audit only."""
    deps = predecessors(spec.id for spec in specs)
    return {
        "audit_only": True,
        "claude": claude,
        "block_reason": block_reason,
        "note": (
            "Every seat is an audit. Builder seats report gaps and do not edit owned product paths. "
            "This orchestrator does not generate the product."
        ),
        "edges_doc": EDGES_DOC,
        "nodes": [
            {
                "id": spec.id,
                "title": spec.title,
                "kind": spec.kind,
                "brief": spec.brief,
                "state": state.get(spec.id, "pending"),
                "depends_on": deps.get(spec.id, []),
            }
            for spec in specs
        ],
        "edges": [{"from": src, "to": dst} for src, dst in edges],
        "state": {spec.id: state.get(spec.id, "pending") for spec in specs},
    }
