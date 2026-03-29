"""Graph-RAG retrieval: select and serialize the right subgraph for a user question.

Strategy selection is based on simple heuristic keyword matching:
- Flow / process / main / overview questions -> condensed graph
- Specific tag mentioned (e.g. P-101, TIC-201) -> neighbourhood of that tag
- Control loop / lazo / controller questions -> control loop subgraph
- Default -> condensed graph (high-level overview)
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import networkx as nx

if TYPE_CHECKING:
    from pid_knowledge_graph.neo4j_store import Neo4jStore


# Regex for ISA-style tag numbers: 1-3 uppercase letters, dash, digits (optional suffix)
_TAG_PATTERN = re.compile(r"\b([A-Z]{1,4}-\d{2,5}[A-Z]?)\b")

# Keywords that suggest the user wants a condensed / flow-level view
_FLOW_KEYWORDS = frozenset({
    "flujo", "proceso", "principal", "flow", "process", "main", "overview",
    "general", "resumen", "summary", "path", "camino", "ruta",
})

# Keywords that suggest the user is asking about a control loop
_LOOP_KEYWORDS = frozenset({
    "lazo", "control", "loop", "controller", "controlador", "pid",
    "transmitter", "transmisor", "valve", "valvula", "sp", "pv",
    "setpoint", "set point",
})


class GraphRAG:
    """Retrieve context from Neo4j based on user questions about a P&ID.

    Parameters
    ----------
    neo4j_store:
        An already-connected :class:`Neo4jStore` instance.
    """

    def __init__(self, neo4j_store: "Neo4jStore") -> None:
        self._store = neo4j_store

    async def retrieve(self, pid_id: str, question: str) -> str:
        """Retrieve relevant graph context for *question* about *pid_id*.

        Returns
        -------
        str
            A human-readable text serialization of the retrieved subgraph
            suitable for inclusion in an LLM prompt.
        """
        question_lower = question.lower()

        # 1. Check for specific tag mentions
        tags = _TAG_PATTERN.findall(question.upper())
        if tags:
            return await self._retrieve_tag_neighbourhood(pid_id, tags)

        # 2. Check for control-loop keywords
        if _LOOP_KEYWORDS & set(question_lower.split()):
            # Try to find a tag within the question for the loop anchor
            # If no tag, fall back to condensed graph with instruments
            return await self._retrieve_condensed(pid_id)

        # 3. Check for flow/process keywords
        if _FLOW_KEYWORDS & set(question_lower.split()):
            return await self._retrieve_condensed(pid_id)

        # 4. Default: condensed graph
        return await self._retrieve_condensed(pid_id)

    async def _retrieve_condensed(self, pid_id: str) -> str:
        """Retrieve and serialize the condensed (equipment-level) graph."""
        graph = await self._store.get_condensed_graph(pid_id)
        if not graph.nodes:
            return f"No graph data found for P&ID '{pid_id}'."
        return _serialize_graph(graph)

    async def _retrieve_tag_neighbourhood(
        self, pid_id: str, tags: list[str],
    ) -> str:
        """Retrieve neighbourhoods for the specified tags and merge them."""
        merged = nx.DiGraph()
        for tag in tags:
            sub = await self._store.get_neighbors(pid_id, tag, depth=2)
            merged = nx.compose(merged, sub)

        if not merged.nodes:
            return (
                f"No nodes found for tag(s) {', '.join(tags)} "
                f"in P&ID '{pid_id}'."
            )
        return _serialize_graph(merged)

    async def _retrieve_control_loop(
        self, pid_id: str, instrument_tag: str,
    ) -> str:
        """Retrieve the control loop anchored at *instrument_tag*."""
        graph = await self._store.get_control_loop(pid_id, instrument_tag)
        if not graph.nodes:
            return (
                f"No control loop found for instrument '{instrument_tag}' "
                f"in P&ID '{pid_id}'."
            )
        return _serialize_graph(graph)


# ---------------------------------------------------------------------------
# Graph serialization helpers
# ---------------------------------------------------------------------------


def _serialize_graph(graph: nx.DiGraph) -> str:
    """Serialize a NetworkX graph into LLM-readable text.

    Format::

        NODES:
        - [Equipment] P-101 (CentrifugalPump): Centrifugal Pump P-101
        - [Instrument] TIC-201 (TemperatureController): TIC-201 (Temperature Indicating Controller)

        CONNECTIONS:
        - P-101 --[FLOW]--> E-101: Process flow from P-101 to E-101
        - TIC-201 --[CONTROLS]--> TV-201: TIC-201 controls TV-201
    """
    lines: list[str] = []

    # Nodes
    lines.append("NODES:")
    for node_id, data in sorted(graph.nodes(data=True), key=lambda x: x[0]):
        node_type = data.get("node_type", "Unknown")
        tag = data.get("tag_number", node_id)
        dexpi_class = data.get("dexpi_class", "")
        label = data.get("label", tag)
        lines.append(f"- [{node_type}] {tag} ({dexpi_class}): {label}")

    # Edges
    lines.append("")
    lines.append("CONNECTIONS:")
    for u, v, data in sorted(graph.edges(data=True), key=lambda x: (x[0], x[1])):
        rel_type = data.get("rel_type", "RELATED")
        u_tag = graph.nodes[u].get("tag_number", u) if u in graph else u
        v_tag = graph.nodes[v].get("tag_number", v) if v in graph else v
        label = data.get("label", "")
        desc = f": {label}" if label else ""
        lines.append(f"- {u_tag} --[{rel_type}]--> {v_tag}{desc}")

    return "\n".join(lines)
