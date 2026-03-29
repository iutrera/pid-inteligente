"""Integration tests that call the FastAPI server via HTTP.

These tests require the API to be running on localhost:8000.
They are automatically skipped when the server is not reachable.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from conftest import API_BASE_URL, _is_api_reachable

pytestmark = pytest.mark.skipif(
    not _is_api_reachable(),
    reason="API not reachable on localhost:8000",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _client() -> httpx.Client:
    return httpx.Client(base_url=API_BASE_URL, timeout=30.0)


def _upload_drawio(client: httpx.Client, drawio_path: Path, pid_id: str) -> httpx.Response:
    """POST /api/graph/build with the given .drawio file."""
    with open(drawio_path, "rb") as f:
        return client.post(
            "/api/graph/build",
            files={"file": (drawio_path.name, f, "application/xml")},
            data={"pid_id": pid_id},
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestHealth:
    """Smoke tests for the health endpoint."""

    def test_health(self) -> None:
        with _client() as c:
            resp = c.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "version" in body


class TestGraphBuild:
    """Tests for graph building and retrieval."""

    def test_build_graph(self, drawio_file: Path, pid_id: str) -> None:
        with _client() as c:
            resp = _upload_drawio(c, drawio_file, pid_id)
        assert resp.status_code == 200
        body = resp.json()
        assert body["pid_id"] == pid_id
        assert body["node_count"] >= 10
        assert body["equipment_count"] >= 3

    def test_get_condensed_graph(self, drawio_file: Path, pid_id: str) -> None:
        with _client() as c:
            # Ensure graph is built first
            _upload_drawio(c, drawio_file, pid_id)
            resp = c.get(f"/api/graph/{pid_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert "nodes" in body
        assert "edges" in body
        assert len(body["edges"]) > 0

    def test_get_detailed_graph(self, drawio_file: Path, pid_id: str) -> None:
        with _client() as c:
            _upload_drawio(c, drawio_file, pid_id)
            condensed = c.get(f"/api/graph/{pid_id}").json()
            detailed = c.get(f"/api/graph/{pid_id}/detail").json()
        assert detailed["nodes"]
        # Detailed graph should have more nodes than condensed
        assert len(detailed["nodes"]) >= len(condensed["nodes"])

    def test_get_drawio_xml(self, drawio_file: Path, pid_id: str) -> None:
        with _client() as c:
            _upload_drawio(c, drawio_file, pid_id)
            resp = c.get(f"/api/graph/{pid_id}/drawio")
        assert resp.status_code == 200
        body = resp.json()
        assert "xml" in body
        assert "mxfile" in body["xml"].lower()


class TestConversion:
    """Tests for the bidirectional conversion endpoints."""

    def test_convert_drawio_to_dexpi(self, drawio_file: Path) -> None:
        with _client() as c:
            with open(drawio_file, "rb") as f:
                resp = c.post(
                    "/api/convert/drawio-to-dexpi",
                    files={"file": (drawio_file.name, f, "application/xml")},
                )
        assert resp.status_code == 200
        content = resp.text
        # Response should be valid DEXPI XML
        assert "PlantModel" in content or "Equipment" in content

    def test_convert_roundtrip(self, drawio_file: Path) -> None:
        """drawio -> dexpi -> drawio: second drawio must be valid XML with mxfile."""
        with _client() as c:
            # Step 1: drawio -> dexpi
            with open(drawio_file, "rb") as f:
                dexpi_resp = c.post(
                    "/api/convert/drawio-to-dexpi",
                    files={"file": (drawio_file.name, f, "application/xml")},
                )
            assert dexpi_resp.status_code == 200
            dexpi_xml = dexpi_resp.text

            # Step 2: dexpi -> drawio
            drawio_resp = c.post(
                "/api/convert/dexpi-to-drawio",
                files={"file": ("converted.xml", dexpi_xml.encode(), "application/xml")},
            )
            assert drawio_resp.status_code == 200
            roundtrip_xml = drawio_resp.text
            assert "mxfile" in roundtrip_xml.lower()


class TestValidation:
    """Tests for the validation endpoint."""

    def test_validate_pid(self, drawio_file: Path) -> None:
        with _client() as c:
            with open(drawio_file, "rb") as f:
                resp = c.post(
                    "/api/validate",
                    files={"file": (drawio_file.name, f, "application/xml")},
                )
        assert resp.status_code == 200
        body = resp.json()
        assert "errors" in body
        assert "total" in body

    def test_validate_detects_errors(self, tmp_path: Path) -> None:
        """A minimal drawio with an equipment node missing tag_number should trigger errors."""
        minimal_drawio = """\
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="test">
  <diagram id="d1" name="Test">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" value="Process" parent="0"/>
        <object label="" dexpi_class="CentrifugalPump" dexpi_component_class="CHBP" id="10">
          <mxCell style="shape=ellipse;" vertex="1" parent="1">
            <mxGeometry x="100" y="100" width="60" height="60" as="geometry"/>
          </mxCell>
        </object>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""
        bad_file = tmp_path / "bad.drawio"
        bad_file.write_text(minimal_drawio, encoding="utf-8")

        with _client() as c:
            with open(bad_file, "rb") as f:
                resp = c.post(
                    "/api/validate",
                    files={"file": ("bad.drawio", f, "application/xml")},
                )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] > 0
        # At least one error should be about missing tag
        error_types = [e["error_type"] for e in body["errors"]]
        assert "missing_tag" in error_types
