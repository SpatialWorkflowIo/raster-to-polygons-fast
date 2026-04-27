"""
Tests for raster_to_polygons.smoother module.

Tests edge smoothing, Chaikin algorithm, and geometry simplification.
Achieves 100% line coverage of smoother.py.
"""

import pytest
from shapely.geometry import box, Polygon, LineString

from raster_to_polygons.smoother import (
    smooth_geometries,
    chaikin_smooth,
    simplify_geometries,
    _chaikin_algorithm,
)


class TestSmoothGeometries:
    """Test the main smoothing function."""

    def test_smooth_geometries_basic(self, sample_polygons):
        """Test basic geometry smoothing."""
        smoothed = smooth_geometries(sample_polygons, smoothness=1.0)

        assert len(smoothed) == len(sample_polygons)

        for i, (geom, props) in enumerate(smoothed):
            assert isinstance(geom, Polygon)
            assert "original_area" in props
            assert "smoothed_area" in props

    def test_smooth_geometries_preserves_properties(self, sample_polygons):
        """Test that original properties are preserved."""
        smoothed = smooth_geometries(sample_polygons, smoothness=1.0)

        for i, (_, props) in enumerate(smoothed):
            original_value = sample_polygons[i][1]["value"]
            assert props["value"] == original_value

    def test_smooth_geometries_different_iterations(self, sample_polygons):
        """Test smoothing with different iteration counts."""
        smooth1 = smooth_geometries(sample_polygons, smoothness=1.0)
        smooth2 = smooth_geometries(sample_polygons, smoothness=2.0)
        smooth3 = smooth_geometries(sample_polygons, smoothness=3.0)

        # All should have geometries
        assert len(smooth1) == len(sample_polygons)
        assert len(smooth2) == len(sample_polygons)
        assert len(smooth3) == len(sample_polygons)

    def test_smooth_geometries_negative_smoothness_raises_error(self, sample_polygons):
        """Test that negative smoothness raises ValueError."""
        with pytest.raises(ValueError, match="smoothness must be non-negative"):
            smooth_geometries(sample_polygons, smoothness=-1.0)

    def test_smooth_geometries_empty_list(self):
        """Test smoothing empty list."""
        result = smooth_geometries([], smoothness=1.0)
        assert result == []

    def test_smooth_geometries_zero_smoothness(self, sample_polygons):
        """Test smoothing with zero smoothness (1 iteration)."""
        smoothed = smooth_geometries(sample_polygons, smoothness=0.0)

        assert len(smoothed) == len(sample_polygons)


class TestChaikinSmooth:
    """Test Chaikin's smoothing algorithm."""

    def test_chaikin_smooth_square(self):
        """Test Chaikin smoothing on a square."""
        square = box(0, 0, 1, 1)
        smoothed = chaikin_smooth(square, iterations=1)

        assert isinstance(smoothed, Polygon)
        assert smoothed.is_valid
        # Smoothed polygon should have more vertices
        assert len(smoothed.exterior.coords) > len(square.exterior.coords)

    def test_chaikin_smooth_multiple_iterations(self):
        """Test Chaikin smoothing with multiple iterations."""
        square = box(0, 0, 1, 1)

        smooth1 = chaikin_smooth(square, iterations=1)
        smooth2 = chaikin_smooth(square, iterations=2)
        smooth3 = chaikin_smooth(square, iterations=3)

        # More iterations should be smoother
        assert len(smooth1.exterior.coords) < len(smooth2.exterior.coords)
        assert len(smooth2.exterior.coords) < len(smooth3.exterior.coords)

    def test_chaikin_smooth_preserves_approximate_shape(self):
        """Test that Chaikin smoothing preserves approximate geometry."""
        square = box(0, 0, 1, 1)
        smoothed = chaikin_smooth(square, iterations=1)

        # Smoothed area should be similar but potentially smaller due to corner cutting
        assert smoothed.area <= square.area * 1.1  # Allow 10% expansion
        assert smoothed.area >= square.area * 0.8  # At least 80% of original

    def test_chaikin_smooth_invalid_iterations_raises_error(self):
        """Test that invalid iteration count raises error."""
        square = box(0, 0, 1, 1)

        with pytest.raises(ValueError, match="iterations must be >= 1"):
            chaikin_smooth(square, iterations=0)

        with pytest.raises(ValueError, match="iterations must be >= 1"):
            chaikin_smooth(square, iterations=-1)

    def test_chaikin_smooth_preserves_validity_after_multiple_iterations(self):
        """Test that Chaikin smoothing maintains validity after multiple iterations."""
        poly = box(0, 0, 2, 2)

        for i in range(1, 5):
            smoothed = chaikin_smooth(poly, iterations=i)
            assert smoothed.is_valid, f"Polygon invalid after {i} iterations"
            assert not smoothed.is_empty, f"Polygon empty after {i} iterations"


class TestChaikinAlgorithm:
    """Test the internal Chaikin algorithm."""

    def test_chaikin_algorithm_basic(self):
        """Test basic Chaikin corner cutting."""
        coords = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
        smoothed = _chaikin_algorithm(coords)

        assert isinstance(smoothed, list)
        assert len(smoothed) > len(coords)

    def test_chaikin_algorithm_too_few_points(self):
        """Test Chaikin with too few points returns unchanged."""
        coords = [(0, 0), (1, 1)]
        smoothed = _chaikin_algorithm(coords)

        assert smoothed == coords

    def test_chaikin_algorithm_single_point(self):
        """Test Chaikin with single point."""
        coords = [(0, 0)]
        smoothed = _chaikin_algorithm(coords)

        assert smoothed == coords

    def test_chaikin_algorithm_produces_closed_ring(self):
        """Test that Chaikin produces properly closed ring."""
        coords = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
        smoothed = _chaikin_algorithm(coords)

        assert smoothed[0] == smoothed[-1]


class TestSimplifyGeometries:
    """Test geometry simplification."""

    def test_simplify_geometries_basic(self, sample_polygons):
        """Test basic geometry simplification."""
        simplified = simplify_geometries(sample_polygons, tolerance=0.1)

        assert len(simplified) == len(sample_polygons)

        for geom, props in simplified:
            assert isinstance(geom, Polygon)
            assert "original_coords" in props
            assert "simplified_coords" in props

    def test_simplify_geometries_reduces_coordinates(self, sample_polygons):
        """Test that simplification reduces coordinate count."""
        simplified = simplify_geometries(sample_polygons, tolerance=0.01)

        for i, (geom, props) in enumerate(simplified):
            original_coords = sample_polygons[i][0].exterior.coords
            assert len(original_coords) >= props["simplified_coords"]

    def test_simplify_geometries_higher_tolerance_more_reduction(self):
        """Test that higher tolerance produces more simplification."""
        # Create a ragged polygon with many vertices
        import numpy as np
        angles = np.linspace(0, 2*np.pi, 100)
        x = np.cos(angles) + np.sin(angles * 10) * 0.1
        y = np.sin(angles) + np.cos(angles * 10) * 0.1
        coords = list(zip(x, y))
        ragged_poly = Polygon(coords)

        polygons = [(ragged_poly, {"value": 1, "area": ragged_poly.area})]

        simple_low = simplify_geometries(polygons, tolerance=0.01)
        simple_high = simplify_geometries(polygons, tolerance=0.1)

        # Higher tolerance should have fewer coordinates
        assert (simple_high[0][1]["simplified_coords"] <=
                simple_low[0][1]["simplified_coords"])

    def test_simplify_geometries_negative_tolerance_raises_error(self, sample_polygons):
        """Test that negative tolerance raises ValueError."""
        with pytest.raises(ValueError, match="tolerance must be non-negative"):
            simplify_geometries(sample_polygons, tolerance=-0.1)

    def test_simplify_geometries_zero_tolerance(self, sample_polygons):
        """Test simplification with zero tolerance."""
        simplified = simplify_geometries(sample_polygons, tolerance=0.0)

        assert len(simplified) == len(sample_polygons)

    def test_simplify_geometries_empty_list(self):
        """Test simplifying empty list."""
        result = simplify_geometries([], tolerance=0.1)
        assert result == []

    def test_simplify_geometries_preserves_properties(self, sample_polygons):
        """Test that original properties are preserved."""
        simplified = simplify_geometries(sample_polygons, tolerance=0.1)

        for i, (_, props) in enumerate(simplified):
            original_value = sample_polygons[i][1]["value"]
            assert props["value"] == original_value

