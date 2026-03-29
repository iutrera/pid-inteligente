# Knowledge Graph Guide

The Knowledge Graph is the core data structure that enables intelligent querying of P&ID diagrams. It transforms the flat XML of a Draw.io file into a richly connected graph of equipment, instruments, piping, and control loops, stored in Neo4j for fast traversal and queried by the LLM via Graph-RAG.

## Two Levels of Graph

The system builds two complementary views of every P&ID:

### Detailed Graph

Contains every element in the P&ID as a node, with fine-grained relationships:

- **Node types**: Equipment, Instrument, PipingComponent, Nozzle, PipingNetworkSegment
- **Relationships**: `HAS_NOZZLE`, `SEND_TO`, `CONTROLS`, `IS_LOCATED_IN`, `CONNECTED_TO`
- **Use case**: Answering specific questions ("What nozzles does T-101 have?", "What instruments control TCV-101?")

### Condensed Graph

A simplified view where equipment items are the primary nodes and piping details are collapsed into direct flow edges:

- **Node types**: Equipment (only)
- **Relationships**: Flow edges (directed) between equipment, control loop edges
- **Use case**: Answering high-level questions ("What is the main process flow?", "How many paths exist from T-101 to HE-101?")

The Graph-RAG system automatically selects which graph level to use based on the user's question.

## How the Graph Is Built

```
.drawio file
    |
    v
  parse_drawio()           -- Extract elements and connections from XML
    |
    v
  build_graph()            -- Create NetworkX DiGraph with nodes and edges
    |                         Nodes carry: tag_number, dexpi_class, node_type,
    |                         design conditions, coordinates
    v
  enrich_labels()          -- Add human-readable labels for the LLM
    |                         e.g., "Pump P-101 (centrifugal, 15 kW)"
    v
  condense_graph()         -- Collapse piping into equipment-to-equipment
    |                         flow edges for the high-level view
    v
  Neo4jStore.load_graph()  -- Persist both detailed and condensed graphs
                              as PidNode nodes with relationships in Neo4j
```

### Programmatic Usage

```python
from pid_knowledge_graph import build_graph, condense_graph, enrich_labels
from pid_knowledge_graph.neo4j_store import Neo4jStore

# Build detailed graph from a .drawio file
detailed = build_graph("my-pid.drawio", pid_id="my-pid")
enrich_labels(detailed)

# Build condensed graph
condensed = condense_graph(detailed)
enrich_labels(condensed)

# Persist to Neo4j
store = Neo4jStore(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="pidinteligente",
)
async with store:
    await store.load_graph("my-pid", detailed)
    await store.load_graph("my-pid_condensed", condensed)
```

## Exploring in Neo4j Browser

### Connect

Open http://localhost:7474 in your browser and log in:

- **Username**: `neo4j`
- **Password**: `pidinteligente`

(These are the defaults from docker-compose.yml.)

### Example Cypher Queries

#### List all equipment

```cypher
MATCH (n:PidNode)
WHERE n.node_type = 'Equipment'
RETURN n.tag_number AS tag, n.dexpi_class AS class, n.label AS label
ORDER BY n.tag_number
```

#### Find everything connected to P-101

```cypher
MATCH (p:PidNode {tag_number: 'P-101'})-[r]-(neighbor)
RETURN p, r, neighbor
```

This returns all nodes directly connected to P-101 (nozzles, piping segments, instruments) and their relationships. The Neo4j browser renders this as an interactive graph.

#### Trace the process flow between two equipment items

```cypher
MATCH path = (a:PidNode {tag_number: 'T-101'})-[:SEND_TO*]->(b:PidNode {tag_number: 'HE-101'})
RETURN path
```

This follows `SEND_TO` edges to find all paths from T-101 to HE-101.

#### Find control loops on a specific equipment

```cypher
MATCH (loop:PidNode {node_type: 'Instrument'})-[:CONTROLS]->(eq:PidNode {tag_number: 'HE-101'})
RETURN loop.tag_number AS instrument, loop.dexpi_class AS class
```

#### Count nodes by type

```cypher
MATCH (n:PidNode)
RETURN n.node_type AS type, count(*) AS count
ORDER BY count DESC
```

#### Find equipment without safety valves

```cypher
MATCH (eq:PidNode)
WHERE eq.node_type = 'Equipment'
  AND eq.dexpi_class IN ['VerticalVessel', 'HorizontalVessel', 'Column', 'Reactor']
  AND NOT EXISTS {
    MATCH (eq)-[:HAS_NOZZLE]->()-[:CONNECTED_TO]->(psv:PidNode)
    WHERE psv.dexpi_class = 'SafetyValve'
  }
RETURN eq.tag_number AS vessel, eq.dexpi_class AS class
```

#### Get the full detailed graph for a P&ID

```cypher
MATCH (n:PidNode {pid_id: 'my-pid'})-[r]->(m:PidNode {pid_id: 'my-pid'})
RETURN n, r, m
```

### Node Properties

Every `PidNode` in Neo4j carries these properties:

| Property | Description | Example |
|----------|-------------|---------|
| `id` | Unique node identifier | `node_10` |
| `pid_id` | Which P&ID this node belongs to | `test-simple` |
| `tag_number` | ISA tag number | `P-101` |
| `node_type` | Category | `Equipment`, `Instrument`, `Nozzle` |
| `dexpi_class` | DEXPI class name | `CentrifugalPump` |
| `label` | Human-readable label for LLM | `Pump P-101 (centrifugal, 15 kW)` |
| `design_pressure` | Design pressure | `10 barg` |
| `design_temperature` | Design temperature | `80 degC` |

### Relationship Types

| Relationship | From | To | Meaning |
|-------------|------|-----|---------|
| `HAS_NOZZLE` | Equipment | Nozzle | Equipment has this connection point |
| `SEND_TO` | Node | Node | Process flow direction |
| `CONTROLS` | Instrument | Equipment/Valve | Instrument controls this element |
| `IS_LOCATED_IN` | Instrument | Equipment | Instrument is on this equipment |
| `CONNECTED_TO` | Nozzle | PipingComponent | Physical pipe connection |
| `FLOW` | Equipment | Equipment | Condensed graph: direct flow edge |

## Semantic Labels

The `enrich_labels()` function generates descriptive labels designed for the LLM. Examples:

- `"Pump P-101 (centrifugal, 15 kW)"`
- `"Tank T-101 (vertical vessel, 10 m3, SS316L)"`
- `"TIC-101 (Temperature Indicating Controller)"`
- `"Heat Exchanger HE-101 (shell & tube, 150 degC)"`

These labels appear in the Graph-RAG context provided to Claude, enabling natural language understanding of the P&ID structure.

## Installation

```bash
cd packages/pid-knowledge-graph
pip install -e ".[dev]"
```

Requirements: Python 3.11+, Neo4j 5+, pyDEXPI, NetworkX, neo4j driver, Pydantic v2.

## Testing

```bash
cd packages/pid-knowledge-graph
pytest                                  # Run all tests
pytest --cov=pid_knowledge_graph        # With coverage
```
