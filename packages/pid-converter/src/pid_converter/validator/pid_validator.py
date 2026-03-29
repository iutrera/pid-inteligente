"""Validate a P&ID model for completeness and consistency.

Checks performed
----------------
* **missing_tag**: Equipment or instrument without a ``tag_number``
* **missing_line_number**: Piping edge without a ``line_number``
* **unconnected_nozzle**: Nozzle not referenced by any piping segment
* **orphan_instrument**: Instrument not connected by any signal line
* **duplicate_tag**: More than one element shares the same ``tag_number``
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from pid_converter.models import DexpiCategory, PidModel


class ErrorType(str, Enum):
    MISSING_TAG = "missing_tag"
    MISSING_LINE_NUMBER = "missing_line_number"
    UNCONNECTED_NOZZLE = "unconnected_nozzle"
    ORPHAN_INSTRUMENT = "orphan_instrument"
    DUPLICATE_TAG = "duplicate_tag"


class ValidationError(BaseModel):
    """A single validation finding."""

    shape_id: str
    error_type: ErrorType
    message: str


def validate_pid(model: PidModel) -> list[ValidationError]:
    """Run all validation checks on a :class:`PidModel`.

    Returns
    -------
    list[ValidationError]
        Possibly-empty list of findings.
    """
    errors: list[ValidationError] = []

    _check_missing_tags(model, errors)
    _check_missing_line_numbers(model, errors)
    _check_unconnected_nozzles(model, errors)
    _check_orphan_instruments(model, errors)
    _check_duplicate_tags(model, errors)

    return errors


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def _check_missing_tags(model: PidModel, errors: list[ValidationError]) -> None:
    """Equipment and instruments must have a non-empty tag_number."""
    for node in model.nodes:
        if node.category in (DexpiCategory.EQUIPMENT, DexpiCategory.INSTRUMENT):
            tag = node.tag_number or node.attributes.get("tag_number", "")
            if not tag.strip():
                errors.append(ValidationError(
                    shape_id=node.id,
                    error_type=ErrorType.MISSING_TAG,
                    message=(
                        f"{node.dexpi_class or 'Element'} (id={node.id}) "
                        f"has no tag_number"
                    ),
                ))


def _check_missing_line_numbers(model: PidModel, errors: list[ValidationError]) -> None:
    """Piping edges (ProcessLine / UtilityLine) must have a line_number."""
    for edge in model.edges:
        if edge.dexpi_class in {"ProcessLine", "UtilityLine", "PipingNetworkSegment"}:
            ln = edge.attributes.get("line_number", "")
            if not ln.strip():
                errors.append(ValidationError(
                    shape_id=edge.id,
                    error_type=ErrorType.MISSING_LINE_NUMBER,
                    message=(
                        f"Piping segment (id={edge.id}, label={edge.label!r}) "
                        f"has no line_number"
                    ),
                ))


def _check_unconnected_nozzles(model: PidModel, errors: list[ValidationError]) -> None:
    """Nozzles should be referenced by at least one topology connection."""
    nozzle_ids = {
        n.id for n in model.nodes if n.category == DexpiCategory.NOZZLE
    }
    if not nozzle_ids:
        return

    # Collect nozzle IDs that appear as endpoints in connections
    connected: set[str] = set()
    for conn in model.connections:
        if conn.from_node_id in nozzle_ids:
            connected.add(conn.from_node_id)
        if conn.to_node_id in nozzle_ids:
            connected.add(conn.to_node_id)

    for nid in sorted(nozzle_ids - connected):
        node = model.node_by_id(nid)
        nozzle_tag = ""
        if node:
            nozzle_tag = node.attributes.get("nozzle_id", "")
        errors.append(ValidationError(
            shape_id=nid,
            error_type=ErrorType.UNCONNECTED_NOZZLE,
            message=(
                f"Nozzle {nozzle_tag!r} (id={nid}) is not connected "
                f"to any piping segment"
            ),
        ))


def _check_orphan_instruments(model: PidModel, errors: list[ValidationError]) -> None:
    """Instruments should be connected via at least one signal line."""
    instrument_ids = {
        n.id for n in model.nodes if n.category == DexpiCategory.INSTRUMENT
    }
    if not instrument_ids:
        return

    # Collect instrument IDs that appear as endpoints of signal-line edges
    connected: set[str] = set()
    for edge in model.edges:
        if edge.dexpi_class == "SignalLine":
            if edge.source_id in instrument_ids:
                connected.add(edge.source_id)
            if edge.target_id in instrument_ids:
                connected.add(edge.target_id)

    # Also check connections
    for conn in model.connections:
        if conn.from_node_id in instrument_ids:
            connected.add(conn.from_node_id)
        if conn.to_node_id in instrument_ids:
            connected.add(conn.to_node_id)

    for iid in sorted(instrument_ids - connected):
        node = model.node_by_id(iid)
        tag = node.tag_number if node else ""
        errors.append(ValidationError(
            shape_id=iid,
            error_type=ErrorType.ORPHAN_INSTRUMENT,
            message=(
                f"Instrument {tag!r} (id={iid}) is not connected "
                f"to any signal line or control loop"
            ),
        ))


def _check_duplicate_tags(model: PidModel, errors: list[ValidationError]) -> None:
    """Tag numbers should be unique within their category."""
    seen: dict[str, list[str]] = {}  # tag -> [node_ids]
    for node in model.nodes:
        if node.category in (DexpiCategory.EQUIPMENT, DexpiCategory.INSTRUMENT, DexpiCategory.PIPING_COMPONENT):
            tag = node.tag_number or node.attributes.get("tag_number", "")
            if tag.strip():
                seen.setdefault(tag, []).append(node.id)

    for tag, ids in seen.items():
        if len(ids) > 1:
            for nid in ids:
                errors.append(ValidationError(
                    shape_id=nid,
                    error_type=ErrorType.DUPLICATE_TAG,
                    message=(
                        f"Tag '{tag}' is duplicated across elements: "
                        f"{', '.join(ids)}"
                    ),
                ))
