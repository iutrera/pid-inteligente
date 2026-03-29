"""Tests for the CLI (Typer app)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from pid_converter.cli import app

runner = CliRunner()
FIXTURES_DIR = Path(__file__).parent / "fixtures"
EXAMPLE_PID = FIXTURES_DIR / "example-pid.drawio"


class TestConvertCommand:
    """Test ``pid-converter convert``."""

    def test_convert_produces_xml(self, tmp_path: Path) -> None:
        out = tmp_path / "output.xml"
        result = runner.invoke(app, ["convert", str(EXAMPLE_PID), "-o", str(out)])
        assert result.exit_code == 0, result.output
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "PlantModel" in content

    def test_convert_missing_file(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["convert", str(tmp_path / "nope.drawio")])
        assert result.exit_code == 1


class TestImportCommand:
    """Test ``pid-converter import``."""

    def test_import_produces_drawio(self, tmp_path: Path) -> None:
        # First convert to get a Proteus XML
        xml_out = tmp_path / "intermediate.xml"
        runner.invoke(app, ["convert", str(EXAMPLE_PID), "-o", str(xml_out)])
        assert xml_out.exists()

        drawio_out = tmp_path / "reimported.drawio"
        result = runner.invoke(app, ["import", str(xml_out), "-o", str(drawio_out)])
        assert result.exit_code == 0, result.output
        assert drawio_out.exists()
        content = drawio_out.read_text(encoding="utf-8")
        assert "mxfile" in content

    def test_import_missing_file(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["import", str(tmp_path / "nope.xml")])
        assert result.exit_code == 1


class TestValidateCommand:
    """Test ``pid-converter validate``."""

    def test_validate_example(self) -> None:
        result = runner.invoke(app, ["validate", str(EXAMPLE_PID)])
        # The example may or may not have validation errors;
        # the command should run without crashing
        assert result.exit_code in (0, 1)

    def test_validate_missing_file(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["validate", str(tmp_path / "nope.drawio")])
        assert result.exit_code == 1
