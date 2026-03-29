"""Conversion routes: Draw.io <-> DEXPI Proteus XML."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import Response

from pid_converter.importer.dexpi_importer import import_dexpi
from pid_converter.mapper.dexpi_mapper import map_to_dexpi
from pid_converter.parser.mxgraph_parser import parse_drawio
from pid_converter.serializer.proteus_serializer import serialize_to_proteus

router = APIRouter(prefix="/api/convert", tags=["convert"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

# These endpoints use file upload/download, so schemas are implicit via
# UploadFile (request) and file Response (response).  OpenAPI docs are
# generated automatically by FastAPI.


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "/drawio-to-dexpi",
    summary="Convert a Draw.io file to DEXPI Proteus XML",
    response_class=Response,
    responses={
        200: {
            "content": {"application/xml": {}},
            "description": "DEXPI Proteus XML file",
        },
    },
)
async def drawio_to_dexpi(file: UploadFile) -> Response:
    """Upload a ``.drawio`` file and receive DEXPI Proteus XML back."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        xml_str = content.decode("utf-8")
        pid_model = parse_drawio(xml_str)
        dexpi_model = map_to_dexpi(pid_model)
        proteus_xml = serialize_to_proteus(dexpi_model)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Conversion failed: {exc}",
        ) from exc

    output_name = file.filename.rsplit(".", 1)[0] + ".xml"
    return Response(
        content=proteus_xml.encode("utf-8"),
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{output_name}"'},
    )


@router.post(
    "/dexpi-to-drawio",
    summary="Convert a DEXPI Proteus XML file to Draw.io format",
    response_class=Response,
    responses={
        200: {
            "content": {"application/xml": {}},
            "description": "Draw.io (.drawio) XML file",
        },
    },
)
async def dexpi_to_drawio(file: UploadFile) -> Response:
    """Upload a DEXPI Proteus XML file and receive a ``.drawio`` file back."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        xml_str = content.decode("utf-8")
        drawio_xml = import_dexpi(xml_str)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Import failed: {exc}",
        ) from exc

    output_name = file.filename.rsplit(".", 1)[0] + ".drawio"
    return Response(
        content=drawio_xml.encode("utf-8"),
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{output_name}"'},
    )
