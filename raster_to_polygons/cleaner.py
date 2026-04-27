"""
Polygon cleaner: sliver removal and boundary validation.

This module provides functions to remove small/"sliver" polygons and validate
polygon geometries based on area, perimeter, and shape metrics.
"""

from typing import List, Tuple, Dict, Any, Optional
from shapely.geometry import Polygon


def remove_slivers(
    polygons_with_props: List[Tuple[Polygon, Dict[str, Any]]],
    min_area: float,
    max_perimeter_area_ratio: Optional[float] = None,
) -> List[Tuple[Polygon, Dict[str, Any]]]:
    """
    Remove small polygons (slivers) from geometry collection.

    Filters out polygons below a minimum area threshold and/or with
    excessive perimeter-to-area ratios (indicating thin, ribbon-like shapes).

    A "sliver" is typically a very small polygon or one with a high
    perimeter-to-area ratio, which often results from rasterization artifacts.

    Args:
        polygons_with_props: List of (Polygon, properties_dict) tuples
        min_area: Minimum acceptable polygon area in map units
        max_perimeter_area_ratio: Optional max perimeter/area ratio to filter
                                  thin/ribbon-like polygons. If None, no
                                  ratio-based filtering applied

    Returns:
        Filtered list with slivers removed

    Raises:
        ValueError: If min_area is negative
        TypeError: If input is not a list of (Polygon, dict) tuples

    Example:
        >>> from shapely.geometry import box
        >>> polys = [(box(0, 0, 1, 1), {'value': 1})]
        >>> cleaned = remove_slivers(polys, min_area=0.5)
        >>> len(cleaned)
        1
    """
    if min_area < 0:
        raise ValueError(f"min_area must be non-negative, got {min_area}")

    filtered = []
    for geom, props in polygons_with_props:
        # Check area threshold
        if geom.area < min_area:
            continue

        # Check perimeter/area ratio if specified
        if max_perimeter_area_ratio is not None:
            if geom.area > 0:
                ratio = geom.length / geom.area
                if ratio > max_perimeter_area_ratio:
                    continue

        filtered.append((geom, props))

    return filtered


def is_valid_polygon(
    geom: Polygon,
    min_area: float = 0.0,
    max_perimeter_area_ratio: Optional[float] = None,
) -> bool:
    """
    Check if a polygon meets validity criteria.

    Validates a polygon based on geometric criteria: validity, minimum area,
    and optionally perimeter-to-area ratio.

    Args:
        geom: Shapely Polygon to validate
        min_area: Minimum acceptable area
        max_perimeter_area_ratio: Optional max perimeter/area ratio

    Returns:
        True if polygon passes all criteria, False otherwise

    Example:
        >>> from shapely.geometry import box
        >>> is_valid_polygon(box(0, 0, 1, 1), min_area=0.1)
        True
    """
    # Check if geometry is valid
    if not geom.is_valid:
        return False

    # Check if empty
    if geom.is_empty:
        return False

    # Check area
    if geom.area < min_area:
        return False

    # Check perimeter/area ratio
    if max_perimeter_area_ratio is not None:
        if geom.area > 0:
            ratio = geom.length / geom.area
            if ratio > max_perimeter_area_ratio:
                return False

    return True


def fill_holes(
    polygons_with_props: List[Tuple[Polygon, Dict[str, Any]]],
) -> List[Tuple[Polygon, Dict[str, Any]]]:
    """
    Fill interior holes in polygons.

    Updates properties to include hole counts and areas.

    Args:
        polygons_with_props: List of (Polygon, properties_dict) tuples

    Returns:
        List with holes filled

    Example:
        >>> # Polygon with hole (Polygon ring with hole)
        >>> filled = fill_holes([(poly_with_hole, props)])
    """
    filled = []
    for geom, props in polygons_with_props:
        # Remove interior rings (holes)
        exterior = Polygon(geom.exterior.coords)

        updated_props = props.copy()
        updated_props["holes"] = len(geom.interiors)

        # Calculate total hole area
        hole_area = 0.0
        for interior in geom.interiors:
            hole_poly = Polygon(interior.coords)
            hole_area += hole_poly.area

        updated_props["hole_area"] = hole_area

        filled.append((exterior, updated_props))

    return filled


def dissolve_by_value(
    polygons_with_props: List[Tuple[Polygon, Dict[str, Any]]],
) -> List[Tuple[Polygon, Dict[str, Any]]]:
    """
    Dissolve adjacent polygons with same raster value.

    Merges geometries where multiple disconnected polygons have the same
    raster value, simplifying output.

    Args:
        polygons_with_props: List of (Polygon, properties_dict) tuples

    Returns:
        List with dissolved polygons grouped by value

    Example:
        >>> from shapely.geometry import box
        >>> polys = [
        ...     (box(0, 0, 1, 1), {'value': 1}),
        ...     (box(1, 0, 2, 1), {'value': 1}),
        ... ]
        >>> dissolved = dissolve_by_value(polys)
        >>> len(dissolved)
        1
    """
    from shapely.ops import unary_union

    if not polygons_with_props:
        return []

    # Group by value
    groups: Dict[float, List[Polygon]] = {}
    for geom, props in polygons_with_props:
        value = props.get("value")
        if value not in groups:
            groups[value] = []
        groups[value].append(geom)

    # Dissolve each group
    dissolved = []
    for value, geoms in groups.items():
        if len(geoms) == 1:
            merged = geoms[0]
        else:
            merged = unary_union(geoms)

        props = {
            "value": value,
            "area": float(merged.area),
            "perimeter": float(merged.length),
            "polygon_count": len(geoms),
        }
        dissolved.append((merged, props))

    return dissolved

