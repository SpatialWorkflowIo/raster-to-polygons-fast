"""
Command-line interface for raster-to-polygons conversion.

Provides a user-friendly CLI tool for converting raster images to vector
polygons with options for sliver removal and edge smoothing.
"""

from pathlib import Path
from typing import Optional

import click

from raster_to_polygons import __version__
from raster_to_polygons.core import raster_to_polygons


@click.command()
@click.argument("input_file", type=click.Path(dir_okay=False), required=False)
@click.argument(
    "output_file",
    type=click.Path(dir_okay=False),
    required=False,
)
@click.option(
    "--band",
    type=int,
    default=1,
    help="Raster band index to convert (1-indexed). Default: 1",
    show_default=True,
)
@click.option(
    "--remove-slivers",
    is_flag=True,
    help="Remove small polygons (slivers) below auto-calculated threshold",
)
@click.option(
    "--min-area",
    type=float,
    default=None,
    help="Minimum polygon area threshold (map units). "
    "Auto-calculated if --remove-slivers is set without this option.",
)
@click.option(
    "--smooth",
    is_flag=True,
    help="Apply edge smoothing to reduce jagged boundaries",
)
@click.option(
    "--smoothness",
    type=float,
    default=1.0,
    help="Smoothing intensity (1.0=light, 3.0=heavy). Ignored if --smooth not set.",
    show_default=True,
)
@click.option(
    "--version",
    is_flag=True,
    help="Show version and exit",
)
def main(
    input_file: Optional[str],
    output_file: Optional[str],
    band: int,
    remove_slivers: bool,
    min_area: Optional[float],
    smooth: bool,
    smoothness: float,
    version: bool,
) -> None:
    """
    Convert raster image to vector polygons.

    Fast, clean GIS raster-to-vector conversion with sliver removal
    and optional edge smoothing.

    \b
    INPUT_FILE:   Path to input raster file (GeoTIFF, JP2, etc.)
    OUTPUT_FILE:  Path to output shapefile or GeoJSON (optional)

    \b
    Examples:
      # Basic conversion with output to shapefile
      raster-to-polygons input.tif output.shp

      # Remove slivers and smooth edges
      raster-to-polygons input.tif output.shp --remove-slivers --smooth

      # Convert specific band with 50 m² minimum area
      raster-to-polygons input.tif output.shp --band 2 \\
        --remove-slivers --min-area 50

      # Heavy smoothing
      raster-to-polygons input.tif output.geojson --smooth --smoothness 3.0
    """
    if version:
        click.echo(f"raster-to-polygons version {__version__}")
        return

    if not input_file:
        click.echo("Error: INPUT_FILE is required (unless using --version)", err=True)
        raise SystemExit(1)

    try:
        click.echo(f"📡 Reading raster: {input_file}", err=True)

        # Validate inputs
        if not Path(input_file).exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        if smoothness < 0:
            raise ValueError(f"Smoothness must be non-negative, got {smoothness}")

        if remove_slivers and min_area is not None and min_area < 0:
            raise ValueError(f"Min area must be non-negative, got {min_area}")

        # Perform conversion
        polygons = raster_to_polygons(
            input_file,
            output_file=output_file,
            band=band,
            remove_slivers=remove_slivers,
            min_area=min_area,
            smooth_edges=smooth,
            smoothness=smoothness,
        )

        click.echo(f"✓ Converted {len(polygons)} polygons", err=True)

        if output_file:
            click.echo(f"✓ Saved to: {output_file}", err=True)
        else:
            # Print summary statistics
            total_area = sum(props["area"] for _, props in polygons)
            avg_area = total_area / len(polygons) if polygons else 0
            click.echo(f"  Total area: {total_area:.2f}", err=True)
            click.echo(f"  Average area: {avg_area:.2f}", err=True)

        click.echo("✓ Done!", err=True)

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise SystemExit(1)
    except ValueError as e:
        click.echo(f"❌ Validation error: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

