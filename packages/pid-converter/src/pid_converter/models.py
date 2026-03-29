"""Internal data models for P&ID representation.

These Pydantic models form the canonical intermediate representation between
Draw.io mxGraph XML and DEXPI Proteus XML.  Every module in pid-converter
reads from or writes to these models.

The DEXPI output side uses the canonical pyDEXPI library classes directly
(``pydexpi.dexpi_classes``).  This module only defines the *intermediate*
models that the mxGraph parser produces and that the mapper consumes.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DexpiCategory(str, Enum):
    """High-level DEXPI component categories."""

    EQUIPMENT = "Equipment"
    PIPING_COMPONENT = "PipingComponent"
    PIPING_NETWORK_SEGMENT = "PipingNetworkSegment"
    NOZZLE = "Nozzle"
    INSTRUMENT = "Instrument"
    SIGNAL_LINE = "SignalLine"
    UNKNOWN = "Unknown"


class FlowDirection(str, Enum):
    """Inferred flow direction for a connection."""

    FORWARD = "forward"
    REVERSE = "reverse"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

class Position(BaseModel):
    """2-D position extracted from mxGeometry."""

    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0


# ---------------------------------------------------------------------------
# Core node models
# ---------------------------------------------------------------------------

class PidNode(BaseModel):
    """A single P&ID element (equipment, instrument, valve, nozzle, ...)."""

    id: str
    label: str = ""
    dexpi_class: str = ""
    dexpi_component_class: str = ""
    category: DexpiCategory = DexpiCategory.UNKNOWN
    tag_number: str = ""
    attributes: dict[str, str] = Field(default_factory=dict)
    position: Position = Field(default_factory=Position)
    parent_layer: str = ""
    style: str = ""


class PidEdge(BaseModel):
    """A connection between two elements (process line, signal line, ...)."""

    id: str
    label: str = ""
    dexpi_class: str = ""
    dexpi_component_class: str = ""
    source_id: str = ""
    target_id: str = ""
    source_point: Position | None = None
    target_point: Position | None = None
    waypoints: list[Position] = Field(default_factory=list)
    attributes: dict[str, str] = Field(default_factory=dict)
    parent_layer: str = ""
    style: str = ""


class Connection(BaseModel):
    """Resolved topological connection between two PidNodes."""

    from_node_id: str
    to_node_id: str
    via_edge_id: str = ""
    flow_direction: FlowDirection = FlowDirection.UNKNOWN


# ---------------------------------------------------------------------------
# Top-level model
# ---------------------------------------------------------------------------

class PidModel(BaseModel):
    """Complete P&ID intermediate representation."""

    nodes: list[PidNode] = Field(default_factory=list)
    edges: list[PidEdge] = Field(default_factory=list)
    connections: list[Connection] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Convenience lookups ---------------------------------------------------

    def node_by_id(self, node_id: str) -> PidNode | None:
        for n in self.nodes:
            if n.id == node_id:
                return n
        return None

    def edges_from(self, node_id: str) -> list[PidEdge]:
        return [e for e in self.edges if e.source_id == node_id]

    def edges_to(self, node_id: str) -> list[PidEdge]:
        return [e for e in self.edges if e.target_id == node_id]

    def nodes_by_category(self, category: DexpiCategory) -> list[PidNode]:
        return [n for n in self.nodes if n.category == category]

    def equipment(self) -> list[PidNode]:
        return self.nodes_by_category(DexpiCategory.EQUIPMENT)

    def instruments(self) -> list[PidNode]:
        return self.nodes_by_category(DexpiCategory.INSTRUMENT)

    def nozzles(self) -> list[PidNode]:
        return self.nodes_by_category(DexpiCategory.NOZZLE)
