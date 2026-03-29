"""Validation route: check a Draw.io P&ID for common errors."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from pid_converter.parser.mxgraph_parser import parse_drawio
from pid_converter.validator.pid_validator import validate_pid

router = APIRouter(prefix="/api/validate", tags=["validate"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ValidationErrorOut(BaseModel):
    """A single validation finding."""

    shape_id: str
    error_type: str
    message: str


class ValidationResponse(BaseModel):
    """List of validation errors (empty if the P&ID is clean)."""

    errors: list[ValidationErrorOut]
    total: int


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=ValidationResponse,
    summary="Validate a Draw.io P&ID file for common design errors",
)
async def validate_pid_endpoint(file: UploadFile) -> ValidationResponse:
    """Upload a ``.drawio`` file and receive a list of validation findings."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        xml_str = content.decode("utf-8")
        pid_model = parse_drawio(xml_str)
        errors = validate_pid(pid_model)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Validation failed: {exc}",
        ) from exc

    error_list = [
        ValidationErrorOut(
            shape_id=e.shape_id,
            error_type=e.error_type.value,
            message=e.message,
        )
        for e in errors
    ]

    return ValidationResponse(errors=error_list, total=len(error_list))
