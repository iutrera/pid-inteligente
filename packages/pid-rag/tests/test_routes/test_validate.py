"""Tests for the /api/validate endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_validate_valid_pid(client: AsyncClient) -> None:
    """POST /api/validate returns validation results for a valid P&ID."""
    from tests.conftest import SAMPLE_DRAWIO_XML

    resp = await client.post(
        "/api/validate",
        files={"file": ("test.drawio", SAMPLE_DRAWIO_XML.encode(), "application/xml")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "errors" in body
    assert "total" in body
    assert isinstance(body["errors"], list)
    assert body["total"] == len(body["errors"])


@pytest.mark.asyncio
async def test_validate_returns_error_structure(client: AsyncClient) -> None:
    """POST /api/validate returns errors with the expected fields."""
    from tests.conftest import SAMPLE_DRAWIO_XML

    resp = await client.post(
        "/api/validate",
        files={"file": ("test.drawio", SAMPLE_DRAWIO_XML.encode(), "application/xml")},
    )
    assert resp.status_code == 200
    body = resp.json()
    for error in body["errors"]:
        assert "shape_id" in error
        assert "error_type" in error
        assert "message" in error


@pytest.mark.asyncio
async def test_validate_empty_file(client: AsyncClient) -> None:
    """POST /api/validate rejects empty files."""
    resp = await client.post(
        "/api/validate",
        files={"file": ("empty.drawio", b"", "application/xml")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_validate_invalid_xml(client: AsyncClient) -> None:
    """POST /api/validate returns 422 for invalid XML."""
    resp = await client.post(
        "/api/validate",
        files={"file": ("bad.drawio", b"<not>valid<xml", "application/xml")},
    )
    assert resp.status_code == 422
