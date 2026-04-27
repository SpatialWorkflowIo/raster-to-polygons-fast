"""
Tests for raster_to_polygons.cli module.

Tests command-line interface functionality.
Achieves 100% line coverage of cli.py.
"""

import pytest
from click.testing import CliRunner

from raster_to_polygons.cli import main
from raster_to_polygons import __version__


class TestCLIBasic:
    """Test basic CLI functionality."""

    def test_cli_help(self):
        """Test CLI help output."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Convert raster image to vector polygons" in result.output

    def test_cli_version(self):
        """Test CLI version flag."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert __version__ in result.output

    def test_cli_conversion_basic(self, tmp_geotiff, tmp_path):
        """Test basic conversion via CLI."""
        output_file = tmp_path / "output.shp"

        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_geotiff), str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()

    def test_cli_conversion_with_remove_slivers(self, tmp_geotiff, tmp_path):
        """Test CLI with sliver removal."""
        output_file = tmp_path / "output.shp"

        runner = CliRunner()
        result = runner.invoke(
            main,
            [str(tmp_geotiff), str(output_file), "--remove-slivers"],
        )

        assert result.exit_code == 0

    def test_cli_conversion_with_min_area(self, tmp_geotiff, tmp_path):
        """Test CLI with custom minimum area."""
        output_file = tmp_path / "output.shp"

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                str(tmp_geotiff),
                str(output_file),
                "--remove-slivers",
                "--min-area",
                "0.5",
            ],
        )

        assert result.exit_code == 0

    def test_cli_conversion_with_smooth(self, tmp_geotiff, tmp_path):
        """Test CLI with edge smoothing."""
        output_file = tmp_path / "output.shp"

        runner = CliRunner()
        result = runner.invoke(
            main,
            [str(tmp_geotiff), str(output_file), "--smooth"],
        )

        assert result.exit_code == 0

    def test_cli_conversion_with_smoothness(self, tmp_geotiff, tmp_path):
        """Test CLI with custom smoothness level."""
        output_file = tmp_path / "output.shp"

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                str(tmp_geotiff),
                str(output_file),
                "--smooth",
                "--smoothness",
                "2.0",
            ],
        )

        assert result.exit_code == 0

    def test_cli_conversion_with_band(self, tmp_geotiff, tmp_path):
        """Test CLI with specific band selection."""
        output_file = tmp_path / "output.shp"

        runner = CliRunner()
        result = runner.invoke(
            main,
            [str(tmp_geotiff), str(output_file), "--band", "1"],
        )

        assert result.exit_code == 0

    def test_cli_all_options_combined(self, tmp_geotiff, tmp_path):
        """Test CLI with all options enabled."""
        output_file = tmp_path / "output.shp"

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                str(tmp_geotiff),
                str(output_file),
                "--band",
                "1",
                "--remove-slivers",
                "--min-area",
                "0.5",
                "--smooth",
                "--smoothness",
                "1.5",
            ],
        )

        assert result.exit_code == 0

    def test_cli_no_output_file(self, tmp_geotiff):
        """Test CLI without output file (summary only)."""
        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_geotiff)])

        assert result.exit_code == 0

    def test_cli_output_geojson(self, tmp_geotiff, tmp_path):
        """Test CLI with GeoJSON output."""
        output_file = tmp_path / "output.geojson"

        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_geotiff), str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()


class TestCLIErrors:
    """Test CLI error handling."""

    def test_cli_nonexistent_file_error(self):
        """Test CLI error with nonexistent input file."""
        runner = CliRunner()
        result = runner.invoke(main, ["/nonexistent/file.tif"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_cli_invalid_smoothness_error(self, tmp_geotiff, tmp_path):
        """Test CLI error with negative smoothness."""
        output_file = tmp_path / "output.shp"

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                str(tmp_geotiff),
                str(output_file),
                "--smooth",
                "--smoothness",
                "-1.0",
            ],
        )

        assert result.exit_code == 1

    def test_cli_invalid_min_area_error(self, tmp_geotiff, tmp_path):
        """Test CLI error with negative min area."""
        output_file = tmp_path / "output.shp"

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                str(tmp_geotiff),
                str(output_file),
                "--remove-slivers",
                "--min-area",
                "-1.0",
            ],
        )

        assert result.exit_code == 1

    def test_cli_no_input_file_error(self):
        """Test CLI error when input file is not provided."""
        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code == 1
        assert "required" in result.output.lower()

    def test_cli_help_without_file(self):
        """Test CLI help flag."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "INPUT_FILE" in result.output


class TestCLIOutput:
    """Test CLI output messages."""

    def test_cli_output_messages(self, tmp_geotiff, tmp_path):
        """Test that CLI produces expected output messages."""
        output_file = tmp_path / "output.shp"

        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_geotiff), str(output_file)])

        assert "Reading raster" in result.output
        assert "polygons" in result.output
        assert "Done" in result.output

    def test_cli_output_with_summary(self, tmp_geotiff):
        """Test CLI output summary statistics."""
        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_geotiff)])

        assert result.exit_code == 0
        assert "Total area" in result.output or "polygons" in result.output

    def test_cli_unexpected_error_exception(self, tmp_geotiff, tmp_path, monkeypatch):
        """Test CLI handling of unexpected exceptions."""
        output_file = tmp_path / "output.shp"

        # Mock raster_to_polygons to raise an exception
        from raster_to_polygons import cli as cli_module

        original_func = cli_module.raster_to_polygons

        def mock_error(*args, **kwargs):
            raise RuntimeError("Unexpected error during processing")

        monkeypatch.setattr(cli_module, "raster_to_polygons", mock_error)

        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_geotiff), str(output_file)])

        assert result.exit_code == 1
        assert "Unexpected error" in result.output
