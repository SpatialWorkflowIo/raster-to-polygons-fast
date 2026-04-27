"""
Polygon smoother: edge smoothing and simplification.

This module provides functions to smooth and simplify polygon boundaries,
reducing jagged edges from rasterization artifacts.
"""

from typing import List, Tuple, Dict, Any
from shapely.geometry import Polygon
from shapely.ops import unary_union


def smooth_geometries(
    polygons_with_props: List[Tuple[Polygon, Dict[str, Any]]],
    smoothness: float = 1.0,
) -> List[Tuple[Polygon, Dict[str, Any]]]:
    """
    Apply smoothing to polygon edges.

    Uses Chaikin's algorithm to smooth polygon boundaries, reducing the
    jagged appearance caused by rasterization. Higher smoothness values
    create smoother (but less accurate) outputs.

    Args:
        polygons_with_props: List of (Polygon, properties_dict) tuples
        smoothness: Smoothing iterations (1.0 = light, 3.0 = heavy).
                   Values > 5 are aggressive and may simplify too much.

    Returns:
        List of geometries with smoothed edges

    Raises:
        ValueError: If smoothness is negative

    Example:
        >>> from shapely.geometry import box
        >>> polys = [(box(0, 0, 1, 1), {'value': 1})]
        >>> smoothed = smooth_geometries(polys, smoothness=1.5)
    """
    if smoothness < 0:
        raise ValueError(f"smoothness must be non-negative, got {smoothness}")

    smoothed = []
    iterations = max(1, int(smoothness))

    for geom, props in polygons_with_props:
        smoothed_geom = chaikin_smooth(geom, iterations)
        props_copy = props.copy()
        props_copy["original_area"] = float(geom.area)
        props_copy["smoothed_area"] = float(smoothed_geom.area)
        smoothed.append((smoothed_geom, props_copy))

    return smoothed


def chaikin_smooth(polygon: Polygon, iterations: int = 1) -> Polygon:
    """
    Apply Chaikin's corner-cutting algorithm to a polygon.

    Iteratively smooths polygon corners by adding points at 1/4 and 3/4
    positions along each edge.

    Args:
        polygon: Shapely Polygon to smooth
        iterations: Number of smoothing iterations (default: 1)

    Returns:
        Smoothed Polygon geometry

    Raises:
        ValueError: If iterations < 1
    """
    if iterations < 1:
        raise ValueError(f"iterations must be >= 1, got {iterations}")

    coords = list(polygon.exterior.coords)

    for _ in range(iterations):
        coords = _chaikin_algorithm(coords)

    return Polygon(coords)


def _chaikin_algorithm(coords: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Single iteration of Chaikin's corner-cutting algorithm.

    Internal helper that performs one round of smoothing on coordinates.

    Args:
        coords: List of (x, y) coordinate tuples

    Returns:
        Smoothed coordinate list
    """
    if len(coords) < 3:
        return coords

    smooth_coords = []

    for i in range(len(coords) - 1):
        p0 = coords[i]
        p1 = coords[(i + 1) % len(coords)]

        # Cut points at 1/4 and 3/4 along edge
        q = (
            p0[0] + 0.25 * (p1[0] - p0[0]),
            p0[1] + 0.25 * (p1[1] - p0[1]),
        )
        r = (
            p0[0] + 0.75 * (p1[0] - p0[0]),
            p0[1] + 0.75 * (p1[1] - p0[1]),
        )

        smooth_coords.append(q)
        smooth_coords.append(r)

    # Close the ring (len(coords) >= 3 guarantees at least one generated point)
    smooth_coords.append(smooth_coords[0])

    return smooth_coords


def simplify_geometries(
    polygons_with_props: List[Tuple[Polygon, Dict[str, Any]]],
    tolerance: float,
) -> List[Tuple[Polygon, Dict[str, Any]]]:
    """
    Simplify polygon geometries using Douglas-Peucker algorithm.

    Reduces the number of coordinates in polygon boundaries by removing
    points that are within tolerance distance of the simplified line.

    Args:
        polygons_with_props: List of (Polygon, properties_dict) tuples
        tolerance: Maximum distance a point can be from simplified line

    Returns:
        List of simplified geometries

    Raises:
        ValueError: If tolerance is negative

    Example:
        >>> from shapely.geometry import box
        >>> polys = [(box(0, 0, 1, 1), {'value': 1})]
        >>> simplified = simplify_geometries(polys, tolerance=0.1)
    """
    if tolerance < 0:
        raise ValueError(f"tolerance must be non-negative, got {tolerance}")

    simplified = []
    for geom, props in polygons_with_props:
        simpl_geom = geom.simplify(tolerance)
        props_copy = props.copy()
        props_copy["original_coords"] = len(geom.exterior.coords)
        props_copy["simplified_coords"] = len(simpl_geom.exterior.coords)
        simplified.append((simpl_geom, props_copy))

    return simplified

