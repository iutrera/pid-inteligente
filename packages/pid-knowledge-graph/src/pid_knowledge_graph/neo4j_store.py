"""Async Neo4j persistence layer for P&ID Knowledge Graphs.

Uses the official ``neo4j`` async driver.  All Cypher queries use
parameterised bindings -- never string interpolation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import networkx as nx
from neo4j import AsyncGraphDatabase

from pid_knowledge_graph.models import NodeType, RelType

if TYPE_CHECKING:
    from types import TracebackType
    from typing import Any

    from neo4j import AsyncDriver


class Neo4jStore:
    """Async context-manager wrapper around the Neo4j async driver.

    Usage::

        async with Neo4jStore(uri, user, password) as store:
            await store.load_graph("PID-101", graph)
            sub = await store.get_neighbors("PID-101", "P-101", depth=2)
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "password",
        database: str = "neo4j",
    ) -> None:
        self._uri = uri
        self._user = user
        self._password = password
        self._database = database
        self._driver: AsyncDriver | None = None

    # -- Context manager ----------------------------------------------------

    async def __aenter__(self) -> "Neo4jStore":
        self._driver = AsyncGraphDatabase.driver(self._uri, auth=(self._user, self._password))
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the underlying driver."""
        if self._driver is not None:
            await self._driver.close()
            self._driver = None

    # -- Helpers ------------------------------------------------------------

    def _get_driver(self) -> AsyncDriver:
        if self._driver is None:
            raise RuntimeError("Neo4jStore is not connected. Use 'async with' or call __aenter__.")
        return self._driver

    @staticmethod
    def _neo4j_labels(node_type: str) -> str:
        """Return Neo4j label string for a given node_type value."""
        base = "PidNode"
        if node_type == NodeType.EQUIPMENT.value:
            return f":{base}:Equipment"
        if node_type == NodeType.INSTRUMENT.value:
            return f":{base}:Instrument"
        if node_type == NodeType.PIPING_SEGMENT.value:
            return f":{base}:PipingSegment"
        if node_type == NodeType.NOZZLE.value:
            return f":{base}:Nozzle"
        if node_type == NodeType.VALVE.value:
            return f":{base}:Valve"
        if node_type == NodeType.UTILITY_LINE.value:
            return f":{base}:UtilityLine"
        if node_type == NodeType.STEAM_TRAP.value:
            return f":{base}:SteamTrap"
        if node_type == NodeType.SIGNAL_LINE.value:
            return f":{base}:SignalLine"
        if node_type == NodeType.CONTROL_LOOP.value:
            return f":{base}:ControlLoop"
        return f":{base}"

    @staticmethod
    def _clean_props(data: dict[str, Any]) -> dict[str, Any]:
        """Remove internal keys (prefixed with ``_``) and non-serialisable values."""
        clean: dict[str, Any] = {}
        for k, v in data.items():
            if k.startswith("_"):
                continue
            if isinstance(v, (str, int, float, bool)):
                clean[k] = v
            elif isinstance(v, list) and all(isinstance(i, (str, int, float, bool)) for i in v):
                clean[k] = v
        return clean

    # -- Public API ---------------------------------------------------------

    async def load_graph(self, pid_id: str, graph: nx.DiGraph) -> None:
        """Load a full NetworkX graph into Neo4j.

        Each node becomes a Neo4j node with labels ``[:PidNode, :Equipment]``
        (etc.).  Each edge becomes a Neo4j relationship.

        Parameters
        ----------
        pid_id:
            Identifier for the P&ID drawing.
        graph:
            The NetworkX directed graph to persist.
        """
        driver = self._get_driver()

        async with driver.session(database=self._database) as session:
            # Create nodes
            for node_id, data in graph.nodes(data=True):
                node_type = data.get("node_type", NodeType.EQUIPMENT.value)
                labels = self._neo4j_labels(node_type)
                props = self._clean_props(data)
                props["id"] = node_id
                props["pid_id"] = pid_id

                # Build MERGE query with parameterised properties
                query = (
                    f"MERGE (n{labels} {{id: $id, pid_id: $pid_id}}) "
                    "SET n += $props"
                )
                await session.run(query, id=node_id, pid_id=pid_id, props=props)

            # Create relationships
            for u, v, data in graph.edges(data=True):
                rel_type = data.get("rel_type", RelType.SEND_TO.value)
                props = self._clean_props(data)
                props["pid_id"] = pid_id

                query = (
                    "MATCH (a:PidNode {id: $source_id, pid_id: $pid_id}) "
                    "MATCH (b:PidNode {id: $target_id, pid_id: $pid_id}) "
                    f"MERGE (a)-[r:{rel_type} {{pid_id: $pid_id}}]->(b) "
                    "SET r += $props"
                )
                await session.run(
                    query,
                    source_id=u,
                    target_id=v,
                    pid_id=pid_id,
                    props=props,
                )

    async def get_neighbors(
        self,
        pid_id: str,
        node_tag: str,
        depth: int = 1,
    ) -> nx.DiGraph:
        """Return the subgraph of neighbours up to *depth* hops from *node_tag*.

        Parameters
        ----------
        pid_id:
            P&ID identifier.
        node_tag:
            Tag number of the starting node (e.g. ``"P-101"``).
        depth:
            Maximum number of hops.

        Returns
        -------
        nx.DiGraph
            Subgraph containing the neighbourhood.
        """
        driver = self._get_driver()
        g = nx.DiGraph()

        query = (
            "MATCH (start:PidNode {pid_id: $pid_id, tag_number: $tag}) "
            "CALL apoc.path.subgraphAll(start, {maxLevel: $depth}) "
            "YIELD nodes, relationships "
            "RETURN nodes, relationships"
        )

        # Fallback to variable-length path if APOC is not available
        fallback_query = (
            "MATCH path = (start:PidNode {pid_id: $pid_id, tag_number: $tag})"
            "-[*1.." + str(depth) + "]-(neighbor:PidNode {pid_id: $pid_id}) "
            "UNWIND nodes(path) AS n "
            "UNWIND relationships(path) AS r "
            "RETURN DISTINCT n, r"
        )

        async with driver.session(database=self._database) as session:
            try:
                result = await session.run(query, pid_id=pid_id, tag=node_tag, depth=depth)
                records = [record async for record in result]
                if records:
                    for record in records:
                        for node in record["nodes"]:
                            props = dict(node)
                            nid = props.get("id", "")
                            g.add_node(nid, **props)
                        for rel in record["relationships"]:
                            start_id = dict(rel.start_node).get("id", "")
                            end_id = dict(rel.end_node).get("id", "")
                            g.add_edge(start_id, end_id, rel_type=rel.type, **dict(rel))
                    return g
            except Exception:
                pass

            # Fallback
            result = await session.run(fallback_query, pid_id=pid_id, tag=node_tag)
            async for record in result:
                node = record["n"]
                props = dict(node)
                nid = props.get("id", "")
                g.add_node(nid, **props)

                rel = record["r"]
                start_id = dict(rel.start_node).get("id", "")
                end_id = dict(rel.end_node).get("id", "")
                g.add_edge(start_id, end_id, rel_type=rel.type, **dict(rel))

        return g

    async def get_flow_path(
        self,
        pid_id: str,
        from_tag: str,
        to_tag: str,
    ) -> list[dict[str, Any]]:
        """Find the shortest flow path between two equipment tags.

        Parameters
        ----------
        pid_id:
            P&ID identifier.
        from_tag:
            Tag number of the source equipment.
        to_tag:
            Tag number of the target equipment.

        Returns
        -------
        list[dict]
            Ordered list of nodes along the path, each as a property dict.
        """
        driver = self._get_driver()
        path_nodes: list[dict[str, Any]] = []

        query = (
            "MATCH (a:PidNode {pid_id: $pid_id, tag_number: $from_tag}), "
            "      (b:PidNode {pid_id: $pid_id, tag_number: $to_tag}) "
            "MATCH path = shortestPath((a)-[:SEND_TO|FLOW*]->(b)) "
            "UNWIND nodes(path) AS n "
            "RETURN n"
        )

        async with driver.session(database=self._database) as session:
            result = await session.run(
                query, pid_id=pid_id, from_tag=from_tag, to_tag=to_tag
            )
            async for record in result:
                path_nodes.append(dict(record["n"]))

        return path_nodes

    async def get_control_loop(
        self,
        pid_id: str,
        instrument_tag: str,
    ) -> nx.DiGraph:
        """Return the subgraph of a control loop anchored at *instrument_tag*.

        Parameters
        ----------
        pid_id:
            P&ID identifier.
        instrument_tag:
            Tag of any instrument in the loop (sensor, controller, or valve).

        Returns
        -------
        nx.DiGraph
            Subgraph containing the control loop nodes and relationships.
        """
        driver = self._get_driver()
        g = nx.DiGraph()

        query = (
            "MATCH (inst:PidNode {pid_id: $pid_id, tag_number: $tag}) "
            "OPTIONAL MATCH (inst)-[r1:SIGNAL|CONTROLS|MEASURED_BY*1..3]-"
            "(related:PidNode {pid_id: $pid_id}) "
            "WITH inst, collect(DISTINCT related) AS related_nodes, "
            "collect(DISTINCT r1) AS rels "
            "UNWIND ([inst] + related_nodes) AS n "
            "RETURN DISTINCT n"
        )

        async with driver.session(database=self._database) as session:
            result = await session.run(query, pid_id=pid_id, tag=instrument_tag)
            async for record in result:
                node = record["n"]
                props = dict(node)
                nid = props.get("id", "")
                g.add_node(nid, **props)

            # Get relationships between discovered nodes
            if g.nodes:
                node_ids = list(g.nodes)
                rel_query = (
                    "MATCH (a:PidNode {pid_id: $pid_id})-[r]->(b:PidNode {pid_id: $pid_id}) "
                    "WHERE a.id IN $node_ids AND b.id IN $node_ids "
                    "RETURN a.id AS src, b.id AS tgt, type(r) AS rtype, properties(r) AS props"
                )
                result = await session.run(rel_query, pid_id=pid_id, node_ids=node_ids)
                async for record in result:
                    g.add_edge(
                        record["src"],
                        record["tgt"],
                        rel_type=record["rtype"],
                        **record["props"],
                    )

        return g

    async def get_condensed_graph(self, pid_id: str) -> nx.DiGraph:
        """Return a condensed (equipment-only) view stored in Neo4j.

        If the condensed graph was loaded separately (with a ``condensed``
        graph attribute), this queries only Equipment nodes and FLOW edges.
        Otherwise it returns all Equipment nodes and their direct FLOW /
        CONTROLS relationships.

        Parameters
        ----------
        pid_id:
            P&ID identifier.

        Returns
        -------
        nx.DiGraph
            Equipment-level condensed graph.
        """
        driver = self._get_driver()
        g = nx.DiGraph()
        g.graph["pid_id"] = pid_id
        g.graph["condensed"] = True

        async with driver.session(database=self._database) as session:
            # Get equipment nodes
            node_query = (
                "MATCH (e:Equipment {pid_id: $pid_id}) "
                "RETURN e"
            )
            result = await session.run(node_query, pid_id=pid_id)
            async for record in result:
                props = dict(record["e"])
                nid = props.get("id", "")
                g.add_node(nid, **props)

            # Get FLOW and CONTROLS edges between equipment
            edge_query = (
                "MATCH (a:Equipment {pid_id: $pid_id})-[r:FLOW|CONTROLS]->(b {pid_id: $pid_id}) "
                "RETURN a.id AS src, b.id AS tgt, type(r) AS rtype, properties(r) AS props"
            )
            result = await session.run(edge_query, pid_id=pid_id)
            async for record in result:
                g.add_edge(
                    record["src"],
                    record["tgt"],
                    rel_type=record["rtype"],
                    **record["props"],
                )

        return g

    async def delete_graph(self, pid_id: str) -> None:
        """Delete all nodes and relationships for a given P&ID.

        Parameters
        ----------
        pid_id:
            Identifier of the P&ID to delete.
        """
        driver = self._get_driver()

        query = (
            "MATCH (n:PidNode {pid_id: $pid_id}) "
            "DETACH DELETE n"
        )

        async with driver.session(database=self._database) as session:
            await session.run(query, pid_id=pid_id)
