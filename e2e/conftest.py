"""Shared fixtures for E2E / integration tests."""

from __future__ import annotations

import socket
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

E2E_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = E2E_DIR / "fixtures"
DRAWIO_FILE = FIXTURES_DIR / "test-simple.drawio"

# ---------------------------------------------------------------------------
# API configuration
# ---------------------------------------------------------------------------

API_BASE_URL = "http://localhost:8000"
PID_ID = "test-simple"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_api_reachable(host: str = "localhost", port: int = 8000) -> bool:
    """Return True if a TCP connection to *host:port* succeeds."""
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Base URL of the running API server."""
    return API_BASE_URL


@pytest.fixture(scope="session")
def pid_id() -> str:
    """P&ID identifier used in tests."""
    return PID_ID


@pytest.fixture(scope="session")
def drawio_file() -> Path:
    """Path to the test-simple.drawio fixture."""
    assert DRAWIO_FILE.exists(), f"Fixture not found: {DRAWIO_FILE}"
    return DRAWIO_FILE


@pytest.fixture(scope="session")
def drawio_xml(drawio_file: Path) -> str:
    """Raw XML content of the test drawio file."""
    return drawio_file.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def api_available() -> bool:
    """Whether the API server is reachable on localhost:8000."""
    return _is_api_reachable()
