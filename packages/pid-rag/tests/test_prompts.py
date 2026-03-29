"""Tests for the engineering system prompt."""

from __future__ import annotations

from pid_rag.prompts.engineering import SYSTEM_PROMPT


def test_system_prompt_is_string() -> None:
    """SYSTEM_PROMPT should be a non-empty string."""
    assert isinstance(SYSTEM_PROMPT, str)
    assert len(SYSTEM_PROMPT) > 100


def test_system_prompt_contains_isa_nomenclature() -> None:
    """SYSTEM_PROMPT should cover ISA 5.1 instrument nomenclature."""
    assert "ISA" in SYSTEM_PROMPT
    assert "5.1" in SYSTEM_PROMPT
    # Check for key ISA function letters
    assert "Temperature" in SYSTEM_PROMPT
    assert "Pressure" in SYSTEM_PROMPT
    assert "Flow" in SYSTEM_PROMPT
    assert "Level" in SYSTEM_PROMPT
    # Check for function letter definitions
    assert "Transmitter" in SYSTEM_PROMPT
    assert "Controller" in SYSTEM_PROMPT
    assert "Indicator" in SYSTEM_PROMPT
    assert "Alarm" in SYSTEM_PROMPT


def test_system_prompt_contains_control_loop_concepts() -> None:
    """SYSTEM_PROMPT should explain control loop concepts."""
    assert "PV" in SYSTEM_PROMPT
    assert "SP" in SYSTEM_PROMPT
    assert "OP" in SYSTEM_PROMPT
    assert "Set Point" in SYSTEM_PROMPT or "setpoint" in SYSTEM_PROMPT.lower()
    assert "control loop" in SYSTEM_PROMPT.lower()


def test_system_prompt_covers_common_errors() -> None:
    """SYSTEM_PROMPT should describe common P&ID design errors."""
    prompt_lower = SYSTEM_PROMPT.lower()
    # Valves without instrumentation
    assert "valve" in prompt_lower
    assert "instrumentation" in prompt_lower or "instrument" in prompt_lower
    # Dead-end lines
    assert "dead" in prompt_lower or "muertas" in prompt_lower
    # Equipment without PSV
    assert "psv" in prompt_lower or "safety valve" in prompt_lower
    # Missing isolation valves
    assert "isolation" in prompt_lower
    # Orphan instruments
    assert "orphan" in prompt_lower


def test_system_prompt_restricts_to_graph_data() -> None:
    """SYSTEM_PROMPT should instruct the LLM to use only provided data."""
    prompt_lower = SYSTEM_PROMPT.lower()
    assert "only" in prompt_lower
    assert "knowledge graph" in prompt_lower or "graph data" in prompt_lower
    assert "not invent" in prompt_lower or "do not" in prompt_lower
