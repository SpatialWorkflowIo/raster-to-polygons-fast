"""
Core raster-to-polygon conversion logic.

This module provides the main functionality for converting raster images
to vector polygon geometries using rasterio and shapely.
"""

from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any, Union
import warnings

import numpy as np
import rasterio
from rasterio.features import shapes
from rasterio.crs import CRS
from shapely.geometry import shape, Polygon, GeometryCollection
from shapely.ops import unary_union


def raster_to_polygons(
    input_file: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None,
    band: int = 1,
    remove_slivers: bool = False,
    min_area: Optional[float] = None,
    smooth_edges: bool = False,
    smoothness: float = 1.0,
) -> List[Tuple[Polygon, Dict[str, Any]]]:
    """
    Convert raster image to vector polygons.

    Converts a raster file to vector polygon geometries, with optional sliver
    removal and edge smoothing. Works with any rasterio-supported format
    (GeoTIFF, JP2, etc.).

    Args:
        input_file: Path to input raster file (GeoTIFF, JP2, etc.)
        output_file: Optional path to save output as shapefile or GeoJSON
        band: Raster band index to convert (1-indexed, default: 1)
        remove_slivers: If True, remove small/invalid polygons (default: False)
        min_area: Minimum polygon area in map units. If None and remove_slivers
                 is True, uses automatic threshold based on pixel size
        smooth_edges: If True, apply edge smoothing to polygons (default: False)
        smoothness: Smoothing factor (1.0 = light, 3.0 = heavy), ignored if
                   smooth_edges is False

    Returns:
        List of (Polygon, properties_dict) tuples. Each polygon represents a
        converted raster region. Properties include 'value' (raster value),
        'area', and 'perimeter'.

    Raises:
        FileNotFoundError: If input raster file does not exist
        ValueError: If band index is invalid or raster has no bands
        rasterio.errors.RasterioIOError: If file cannot be read by rasterio

    Example:
        >>> polygons = raster_to_polygons(
        ...     'input.tif',
        ...     output_file='output.shp',
        ...     remove_slivers=True,
        ...     smooth_edges=True
        ... )
        >>> print(f"Converted {len(polygons)} polygons")
    """
    from raster_to_polygons.cleaner import remove_slivers as _remove_slivers_func

    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Raster file not found: {input_path}")

    with rasterio.open(input_path) as src:
        if src.count == 0:
            raise ValueError("Raster has no bands")
        if band < 1 or band > src.count:
            raise ValueError(
                f"Band index {band} out of range. Raster has {src.count} bands."
            )

        # Read the specified band
        data = src.read(band)
        crs = src.crs
        transform = src.transform

        # Get nodata value if defined
        nodata = src.nodata

    # Convert raster to polygons
    polygons_with_props = _raster_to_shapes(data, transform, crs, nodata)

     # Apply sliver removal if requested
    if remove_slivers:
        if min_area is None:
            # Auto-compute threshold based on pixel size
            with rasterio.open(input_path) as src:
                pixel_area = abs(src.transform.a * src.transform.e)
                min_area = pixel_area * 4  # 4 pixels minimum
        polygons_with_props = _remove_slivers_func(polygons_with_props, min_area)

    # Apply smoothing if requested
    if smooth_edges:
        from raster_to_polygons.smoother import smooth_geometries
        polygons_with_props = smooth_geometries(polygons_with_props, smoothness)

    # Save to file if output specified
    if output_file is not None:
        _save_polygons(polygons_with_props, output_file, crs)

    return polygons_with_props


def raster_to_features(
    input_file: Union[str, Path],
    band: int = 1,
    remove_slivers: bool = False,
    min_area: Optional[float] = None,
    smooth_edges: bool = False,
    smoothness: float = 1.0,
) -> List[Dict[str, Any]]:
    """
    Convert raster to GeoJSON-like features.

    Returns features in GeoJSON format (geometry + properties).

    Args:
        input_file: Path to input raster file
        band: Raster band index (1-indexed)
        remove_slivers: Remove small polygons
        min_area: Minimum polygon area in map units
        smooth_edges: Apply edge smoothing
        smoothness: Smoothing factor

    Returns:
        List of GeoJSON feature dicts with 'geometry' and 'properties' keys

    Example:
        >>> features = raster_to_features('input.tif', remove_slivers=True)
        >>> for feat in features:
        ...     print(feat['properties']['value'])
    """
    polygons = raster_to_polygons(
        input_file,
        band=band,
        remove_slivers=remove_slivers,
        min_area=min_area,
        smooth_edges=smooth_edges,
        smoothness=smoothness,
    )

    features = []
    for geom, props in polygons:
        feature = {
            "type": "Feature",
            "geometry": geom.__geo_interface__,
            "properties": props,
        }
        features.append(feature)

    return features


def _raster_to_shapes(
    data: np.ndarray,
    transform: Any,
    crs: Optional[CRS],
    nodata: Optional[float] = None,
) -> List[Tuple[Polygon, Dict[str, Any]]]:
    """
    Convert numpy raster array to polygons.

    Internal function that uses rasterio.features.shapes to extract
    polygon geometries from a raster array.

    Args:
        data: 2D numpy array with raster data
        transform: Rasterio affine transform
        crs: Coordinate reference system
        nodata: NoData value to ignore

    Returns:
        List of (geometry, properties) tuples
    """
    polygons_with_props = []

    # Extract shapes from raster
    for geom, value in shapes(data.astype(np.uint8), transform=transform):
        if nodata is not None and value == nodata:
            continue

        try:
            polygon = shape(geom)
            if not polygon.is_valid:
                # Try to fix invalid geometries
                polygon = polygon.buffer(0)
            if polygon.is_empty:
                continue

            props = {
                "value": float(value),
                "area": float(polygon.area),
                "perimeter": float(polygon.length),
            }
            polygons_with_props.append((polygon, props))
        except Exception as e:
            warnings.warn(f"Failed to convert shape for value {value}: {e}")
            continue

    return polygons_with_props


def _save_polygons(
    polygons_with_props: List[Tuple[Polygon, Dict[str, Any]]],
    output_file: Union[str, Path],
    crs: Optional[CRS],
) -> None:
    """
    Save polygons to shapefile or GeoJSON.

    Internal function to persist polygon results to disk.

    Args:
        polygons_with_props: List of (geometry, properties) tuples
        output_file: Output file path (.shp or .geojson)
        crs: Coordinate reference system

    Raises:
        ValueError: If output format is not supported
    """
    import json

    import fiona

    output_path = Path(output_file)
    output_format = output_path.suffix.lower()

    if not polygons_with_props:
        raise ValueError("No polygons to save")

    if output_format == ".shp":
        # For shapefiles, we need all records to have same schema
        # So we'll only use the basic properties
        schema = {
            "geometry": "Polygon",
            "properties": {
                "value": "float",
                "area": "float",
                "perimeter": "float",
            },
        }
        with fiona.open(
            output_path,
            "w",
            driver="ESRI Shapefile",
            schema=schema,
            crs=crs,
        ) as dst:
            for geom, props in polygons_with_props:
                # Extract only schema-compatible properties
                basic_props = {
                    "value": props.get("value", 0.0),
                    "area": props.get("area", 0.0),
                    "perimeter": props.get("perimeter", 0.0),
                }
                dst.write(
                    {
                        "geometry": geom.__geo_interface__,
                        "properties": basic_props,
                    }
                )
    elif output_format in [".geojson", ".json"]:
        # Save as GeoJSON (supports all properties)
        features = []
        for geom, props in polygons_with_props:
            features.append(
                {
                    "type": "Feature",
                    "geometry": geom.__geo_interface__,
                    "properties": props,
                }
            )
        geojson = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": str(crs)}}
            if crs
            else None,
            "features": features,
        }
        with open(output_path, "w") as f:
            json.dump(geojson, f, indent=2)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")

