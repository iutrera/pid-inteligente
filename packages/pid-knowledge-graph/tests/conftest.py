"""Shared fixtures for pid-knowledge-graph tests."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from pid_knowledge_graph.graph_builder import build_graph, build_graph_from_drawio

if TYPE_CHECKING:
    import networkx as nx


FIXTURES_DIR = Path(__file__).parent / "fixtures"
EXAMPLE_PID = FIXTURES_DIR / "example-pid.drawio"


@pytest.fixture()
def example_drawio_path() -> Path:
    """Return the path to the example P&ID .drawio fixture."""
    assert EXAMPLE_PID.exists(), f"Fixture not found: {EXAMPLE_PID}"
    return EXAMPLE_PID


@pytest.fixture()
def detailed_graph(example_drawio_path: Path) -> nx.DiGraph:
    """Build and return the detailed graph from the example P&ID via drawio parser."""
    return build_graph_from_drawio(example_drawio_path, pid_id="PID-101-001")


@pytest.fixture()
def sample_dexpi_model():
    """Build a minimal DexpiModel in-memory for testing the dexpi path.

    This constructs a small but realistic model with:
    - 2 equipment items (a vessel and a pump) with nozzles
    - 1 piping segment connecting them
    - 1 instrument (ProcessInstrumentationFunction)
    """
    from pydexpi.dexpi_classes.dexpiModel import DexpiModel, ConceptualModel
    from pydexpi.dexpi_classes import equipment as eq_mod
    from pydexpi.dexpi_classes import piping as pip_mod
    from pydexpi.dexpi_classes import instrumentation as inst_mod

    # --- Equipment: Vessel V-100 ---
    nozzle_v1 = eq_mod.Nozzle(id="nozzle-v1")
    vessel = eq_mod.Vessel(
        id="vessel-100",
        tagName="V-100",
        tagNamePrefix="V",
        tagNameSequenceNumber="100",
        nozzles=[nozzle_v1],
    )

    # --- Equipment: Pump P-100 ---
    nozzle_p1 = eq_mod.Nozzle(id="nozzle-p1")
    pump = eq_mod.CentrifugalPump(
        id="pump-100",
        tagName="P-100",
        tagNamePrefix="P",
        tagNameSequenceNumber="100",
        nozzles=[nozzle_p1],
    )

    # --- Piping: connection between vessel and pump ---
    conn = pip_mod.PipingConnection(
        sourceItem=nozzle_v1,
        targetItem=nozzle_p1,
    )
    segment = pip_mod.PipingNetworkSegment(
        id="seg-1",
        connections=[conn],
        items=[],
    )
    piping_system = pip_mod.PipingNetworkSystem(
        id="pns-1",
        fluidCode="PROCESS",
        segments=[segment],
    )

    # --- Instrumentation: TIC-101 ---
    instr_fn = inst_mod.ProcessInstrumentationFunction(
        id="tic-101",
        processInstrumentationFunctionCategory="TIC",
        processInstrumentationFunctionNumber="101",
    )

    # --- Assemble the model ---
    conceptual = ConceptualModel(
        taggedPlantItems=[vessel, pump],
        pipingNetworkSystems=[piping_system],
        processInstrumentationFunctions=[instr_fn],
    )

    model = DexpiModel(conceptualModel=conceptual)
    return model
