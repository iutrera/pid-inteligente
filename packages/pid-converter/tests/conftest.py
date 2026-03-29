"""Shared test fixtures for pid-converter."""

from __future__ import annotations

from pathlib import Path

import pytest

from pid_converter.models import PidModel
from pid_converter.parser import parse_drawio

FIXTURES_DIR = Path(__file__).parent / "fixtures"
EXAMPLE_PID = FIXTURES_DIR / "example-pid.drawio"


@pytest.fixture()
def example_pid_path() -> Path:
    """Path to the example P&ID .drawio fixture."""
    return EXAMPLE_PID


@pytest.fixture()
def parsed_model(example_pid_path: Path) -> PidModel:
    """Pre-parsed PidModel from the example P&ID."""
    return parse_drawio(example_pid_path)
