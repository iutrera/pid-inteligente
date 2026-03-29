"""Knowledge Graph routes: build, query, and retrieve P&ID graphs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from lxml import etree

from pid_knowledge_graph import build_graph, condense_graph, enrich_labels

router = APIRouter(prefix="/api/graph", tags=["graph"])


def _apply_layout_to_xml(xml_str: str, pid_model: Any) -> str:
    """Update coordinates in the .drawio XML from a laid-out PidModel.

    Walks the XML tree and for each <object> whose id matches a node in
    the model, updates the <mxGeometry> x/y/width/height to the computed
    layout values.
    """
    tree = etree.fromstring(xml_str.encode())  # noqa: S320
    node_map = {n.id: n for n in pid_model.nodes}

    for obj in tree.iter("object"):
        oid = obj.get("id", "")
        node = node_map.get(oid)
        if not node or not node.position:
            continue

        pos = node.position
        if pos.x is None and pos.y is None:
            continue

        cell = obj.find("mxCell")
        if cell is None:
            continue
        geo = cell.find("mxGeometry")
        if geo is None:
            continue

        # Only update vertex geometry (not edges)
        if cell.get("edge") == "1":
            continue

        if pos.x is not None:
            geo.set("x", str(int(pos.x)))
        if pos.y is not None:
            geo.set("y", str(int(pos.y)))
        if pos.width is not None:
            geo.set("width", str(int(pos.width)))
        if pos.height is not None:
            geo.set("height", str(int(pos.height)))

    return etree.tostring(tree, pretty_print=True, xml_declaration=True,
                          encoding="UTF-8").decode("utf-8")


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class GraphBuildStats(BaseModel):
    """Statistics returned after building a Knowledge Graph."""

    pid_id: str = Field(..., description="Identifier of the P&ID")
    node_count: int = Field(..., description="Total nodes in the detailed graph")
    edge_count: int = Field(..., description="Total edges in the detailed graph")
    equipment_count: int = Field(..., description="Number of equipment nodes")
    instrument_count: int = Field(..., description="Number of instrument nodes")


class GraphNodeOut(BaseModel):
    """A single node in the graph response."""

    id: str
    tag: str = ""
    type: str = ""
    label: str = ""
    extra: dict[str, Any] = Field(default_factory=dict)


class GraphEdgeOut(BaseModel):
    """A single edge in the graph response."""

    source: str
    target: str
    type: str = ""
    label: str = ""


class GraphResponse(BaseModel):
    """Full graph payload returned by query endpoints."""

    nodes: list[GraphNodeOut]
    edges: list[GraphEdgeOut]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _graph_to_response(graph: Any) -> GraphResponse:
    """Convert a NetworkX DiGraph to the API response schema."""
    nodes: list[GraphNodeOut] = []
    for node_id, data in graph.nodes(data=True):
        extra = {
            k: v for k, v in data.items()
            if k not in {"pid_id", "tag_number", "node_type", "label"}
            and not k.startswith("_")
            and isinstance(v, (str, int, float, bool))
        }
        nodes.append(GraphNodeOut(
            id=node_id,
            tag=data.get("tag_number", ""),
            type=data.get("node_type", ""),
            label=data.get("label", ""),
            extra=extra,
        ))

    edges: list[GraphEdgeOut] = []
    for u, v, data in graph.edges(data=True):
        edges.append(GraphEdgeOut(
            source=u,
            target=v,
            type=data.get("rel_type", ""),
            label=data.get("label", ""),
        ))

    return GraphResponse(nodes=nodes, edges=edges)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "/build",
    response_model=GraphBuildStats,
    summary="Build a Knowledge Graph from a Draw.io P&ID file",
)
async def build_graph_endpoint(
    request: Request,
    file: UploadFile,
    pid_id: str = Form(default=""),
) -> GraphBuildStats:
    """Upload a ``.drawio`` file to build its Knowledge Graph and store it in Neo4j."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    effective_pid_id = pid_id or file.filename.rsplit(".", 1)[0]

    try:
        # Apply auto-layout to the P&ID for better visualization
        if not hasattr(request.app.state, "drawio_cache"):
            request.app.state.drawio_cache = {}

        try:
            from pid_converter.parser.mxgraph_parser import parse_drawio
            from pid_converter.layout import layout_pid

            pid_model = parse_drawio(content.decode("utf-8"))
            layout_pid(pid_model)
            # Apply the computed coordinates back to the original XML
            laid_out_xml = _apply_layout_to_xml(content.decode("utf-8"), pid_model)
            request.app.state.drawio_cache[effective_pid_id] = laid_out_xml
        except Exception:
            # Fallback: cache original XML if layout fails
            request.app.state.drawio_cache[effective_pid_id] = content.decode("utf-8")

        # Write to temp file for graph builder (needs file path)
        import tempfile, os
        with tempfile.NamedTemporaryFile(
            suffix=".drawio", delete=False, mode="wb"
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Build detailed graph directly from .drawio (most complete path)
            detailed = build_graph(tmp_path, pid_id=effective_pid_id)
            enrich_labels(detailed)
        finally:
            os.unlink(tmp_path)

        # Build condensed graph
        condensed = condense_graph(detailed)
        enrich_labels(condensed)

        # Load into Neo4j
        neo4j_store = request.app.state.neo4j_store
        await neo4j_store.load_graph(effective_pid_id, detailed)
        await neo4j_store.load_graph(f"{effective_pid_id}_condensed", condensed)

    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Graph build failed: {exc}",
        ) from exc

    # Count equipment and instruments
    equipment_count = sum(
        1 for _, d in detailed.nodes(data=True)
        if d.get("node_type") == "Equipment"
    )
    instrument_count = sum(
        1 for _, d in detailed.nodes(data=True)
        if d.get("node_type") == "Instrument"
    )

    return GraphBuildStats(
        pid_id=effective_pid_id,
        node_count=detailed.number_of_nodes(),
        edge_count=detailed.number_of_edges(),
        equipment_count=equipment_count,
        instrument_count=instrument_count,
    )


@router.get(
    "/{pid_id}/drawio",
    summary="Get the raw .drawio XML for rendering in a viewer",
)
async def get_drawio_xml(request: Request, pid_id: str) -> dict:
    """Return the raw Draw.io XML so the frontend can render it."""
    cache = getattr(request.app.state, "drawio_cache", {})
    xml = cache.get(pid_id)
    if not xml:
        raise HTTPException(status_code=404, detail=f"No .drawio XML cached for '{pid_id}'.")
    return {"pid_id": pid_id, "xml": xml}


@router.get(
    "/{pid_id}",
    response_model=GraphResponse,
    summary="Get the condensed (equipment-level) graph for a P&ID",
)
async def get_condensed_graph(request: Request, pid_id: str) -> GraphResponse:
    """Return the condensed graph (equipment nodes + flow edges) as JSON."""
    neo4j_store = request.app.state.neo4j_store
    try:
        # Fetch the detailed graph and condense on-the-fly
        detailed = await _fetch_detailed_graph(neo4j_store, pid_id)
        graph = condense_graph(detailed)
        enrich_labels(graph)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not graph.nodes:
        raise HTTPException(status_code=404, detail=f"No graph found for pid_id '{pid_id}'.")

    return _graph_to_response(graph)


@router.get(
    "/{pid_id}/detail",
    response_model=GraphResponse,
    summary="Get the detailed graph for a P&ID",
)
async def get_detailed_graph(request: Request, pid_id: str) -> GraphResponse:
    """Return the full detailed graph (all nodes and edges) as JSON.

    Queries Neo4j for all PidNode nodes and their relationships for this pid_id.
    If the store has a ``get_detailed_graph`` method, it is used; otherwise
    the driver is accessed directly.
    """
    neo4j_store = request.app.state.neo4j_store
    try:
        detailed = await _fetch_detailed_graph(neo4j_store, pid_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not detailed.nodes:
        raise HTTPException(status_code=404, detail=f"No graph found for pid_id '{pid_id}'.")

    return _graph_to_response(detailed)


async def _fetch_detailed_graph(neo4j_store: Any, pid_id: str) -> Any:
    """Fetch the detailed graph from Neo4j.

    Supports both a ``get_detailed_graph`` method (e.g. in mocks/tests) and
    direct driver access for production Neo4jStore instances.
    """
    import networkx as nx

    # Check for a dedicated method first (useful for testing/mocks)
    if hasattr(neo4j_store, "get_detailed_graph"):
        return await neo4j_store.get_detailed_graph(pid_id)

    # Fall back to direct Cypher queries
    driver = neo4j_store._get_driver()
    detailed = nx.DiGraph()

    async with driver.session(database=neo4j_store._database) as session:
        # Get all nodes
        result = await session.run(
            "MATCH (n:PidNode {pid_id: $pid_id}) RETURN n",
            pid_id=pid_id,
        )
        async for record in result:
            props = dict(record["n"])
            nid = props.get("id", "")
            detailed.add_node(nid, **props)

        # Get all relationships
        result = await session.run(
            "MATCH (a:PidNode {pid_id: $pid_id})-[r]->(b:PidNode {pid_id: $pid_id}) "
            "RETURN a.id AS src, b.id AS tgt, type(r) AS rtype, properties(r) AS props",
            pid_id=pid_id,
        )
        async for record in result:
            edge_props = dict(record["props"]) if record["props"] else {}
            edge_props.pop("rel_type", None)  # avoid duplicate kwarg
            detailed.add_edge(
                record["src"],
                record["tgt"],
                rel_type=record["rtype"],
                **edge_props,
            )

    return detailed
