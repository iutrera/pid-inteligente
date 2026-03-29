"""Tests for the /api/convert endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_drawio_to_dexpi(client: AsyncClient) -> None:
    """POST /api/convert/drawio-to-dexpi converts a .drawio file to DEXPI XML."""
    from tests.conftest import SAMPLE_DRAWIO_XML

    resp = await client.post(
        "/api/convert/drawio-to-dexpi",
        files={"file": ("test.drawio", SAMPLE_DRAWIO_XML.encode(), "application/xml")},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/xml"
    body = resp.text
    assert "PlantModel" in body
    assert "Equipment" in body


@pytest.mark.asyncio
async def test_drawio_to_dexpi_empty_file(client: AsyncClient) -> None:
    """POST /api/convert/drawio-to-dexpi rejects empty files."""
    resp = await client.post(
        "/api/convert/drawio-to-dexpi",
        files={"file": ("empty.drawio", b"", "application/xml")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_dexpi_to_drawio(client: AsyncClient) -> None:
    """POST /api/convert/dexpi-to-drawio converts a DEXPI XML to .drawio."""
    # First convert to DEXPI to get a valid Proteus XML
    from tests.conftest import SAMPLE_DRAWIO_XML

    resp = await client.post(
        "/api/convert/drawio-to-dexpi",
        files={"file": ("test.drawio", SAMPLE_DRAWIO_XML.encode(), "application/xml")},
    )
    assert resp.status_code == 200
    dexpi_xml = resp.content

    # Now convert back
    resp2 = await client.post(
        "/api/convert/dexpi-to-drawio",
        files={"file": ("test.xml", dexpi_xml, "application/xml")},
    )
    assert resp2.status_code == 200
    assert resp2.headers["content-type"] == "application/xml"
    body = resp2.text
    assert "mxfile" in body or "mxGraphModel" in body


@pytest.mark.asyncio
async def test_dexpi_to_drawio_empty_file(client: AsyncClient) -> None:
    """POST /api/convert/dexpi-to-drawio rejects empty files."""
    resp = await client.post(
        "/api/convert/dexpi-to-drawio",
        files={"file": ("empty.xml", b"", "application/xml")},
    )
    assert resp.status_code == 400
