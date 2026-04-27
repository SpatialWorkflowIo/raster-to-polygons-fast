"""
Pytest fixtures and configuration for raster-to-polygons tests.

Provides reusable test fixtures including sample raster files and geometries.
"""

import numpy as np
import pytest
import rasterio
from pathlib import Path
from rasterio.transform import Affine
from shapely.geometry import Polygon, box


@pytest.fixture
def tmp_geotiff(tmp_path):
    """
    Create a temporary test GeoTIFF file.

    Generates a simple 10x10 GeoTIFF with distinct regions for testing
    raster-to-polygon conversion.

    The output has:
    - Upper left: value 1 (5x5 region)
    - Upper right: value 2 (5x5 region)
    - Lower left: value 0 (background)
    - Lower right: value 3 (5x5 region)

    Yields:
        Path to temporary GeoTIFF file
    """
    output_path = tmp_path / "test.tif"

    # Create a simple test raster
    data = np.array(
        [
            [1, 1, 1, 1, 1, 2, 2, 2, 2, 2],
            [1, 1, 1, 1, 1, 2, 2, 2, 2, 2],
            [1, 1, 1, 1, 1, 2, 2, 2, 2, 2],
            [1, 1, 1, 1, 1, 2, 2, 2, 2, 2],
            [1, 1, 1, 1, 1, 2, 2, 2, 2, 2],
            [0, 0, 0, 0, 0, 3, 3, 3, 3, 3],
            [0, 0, 0, 0, 0, 3, 3, 3, 3, 3],
            [0, 0, 0, 0, 0, 3, 3, 3, 3, 3],
            [0, 0, 0, 0, 0, 3, 3, 3, 3, 3],
            [0, 0, 0, 0, 0, 3, 3, 3, 3, 3],
        ],
        dtype=np.uint8,
    )

    transform = Affine.identity()

    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype,
        transform=transform,
        crs="EPSG:4326",
    ) as dst:
        dst.write(data, 1)

    yield output_path


@pytest.fixture
def sample_polygons():
    """
    Create sample polygons with properties for testing.

    Returns:
        List of (Polygon, properties_dict) tuples
    """
    polygons = [
        (box(0, 0, 2, 2), {"value": 1, "area": 4.0, "perimeter": 8.0}),
        (box(2, 0, 3, 1), {"value": 2, "area": 1.0, "perimeter": 4.0}),
        (box(0, 2, 1, 3), {"value": 3, "area": 1.0, "perimeter": 4.0}),
    ]
    return polygons


@pytest.fixture
def small_polygon():
    """
    Create a very small polygon (sliver) for testing removal.

    Returns:
        (Polygon, properties_dict) tuple with tiny area
    """
    # Very thin rectangle - a classic sliver
    tiny_poly = Polygon([(0, 0), (10, 0), (10, 0.01), (0, 0.01), (0, 0)])
    props = {"value": 1, "area": tiny_poly.area, "perimeter": tiny_poly.length}
    return (tiny_poly, props)


@pytest.fixture
def invalid_polygon():
    """
    Create an invalid polygon for testing validation.

    Returns:
        (Invalid Polygon, properties_dict) tuple
    """
    # Self-intersecting polygon is invalid
    invalid_poly = Polygon([(0, 0), (1, 1), (1, 0), (0, 1)])
    props = {"value": 1, "area": 0, "perimeter": 0}
    return (invalid_poly, props)


@pytest.fixture
def polygon_with_hole():
    """
    Create a polygon with an interior hole.

    Returns:
        (Polygon with hole, properties_dict) tuple
    """
    exterior = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
    interior = [(2, 2), (8, 2), (8, 8), (2, 8), (2, 2)]
    poly = Polygon(exterior, [interior])
    props = {"value": 1, "area": poly.area, "perimeter": poly.length}
    return (poly, props)


@pytest.fixture
def empty_geotiff(tmp_path):
    """
    Create an empty GeoTIFF (all NoData values).

    Yields:
        Path to empty GeoTIFF file
    """
    output_path = tmp_path / "empty.tif"

    data = np.full((10, 10), 255, dtype=np.uint8)
    transform = Affine.identity()

    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype=data.dtype,
        transform=transform,
        crs="EPSG:4326",
        nodata=255,
    ) as dst:
        dst.write(data, 1)

    yield output_path


@pytest.fixture
def single_pixel_geotiff(tmp_path):
    """
    Create a single-pixel GeoTIFF.

    Yields:
        Path to single-pixel GeoTIFF file
    """
    output_path = tmp_path / "pixel.tif"

    data = np.array([[5]], dtype=np.uint8)
    transform = Affine.identity()

    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=1,
        width=1,
        count=1,
        dtype=data.dtype,
        transform=transform,
        crs="EPSG:4326",
    ) as dst:
        dst.write(data, 1)

    yield output_path

