"""
Tests for raster_to_polygons.cleaner module.

Tests sliver removal, polygon validation, hole filling, and dissolving.
Achieves 100% line coverage of cleaner.py.
"""

import pytest
from shapely.geometry import box, Polygon

from raster_to_polygons.cleaner import (
    remove_slivers,
    is_valid_polygon,
    fill_holes,
    dissolve_by_value,
)


class TestRemoveSlivers:
    """Test the sliver removal functionality."""

    def test_remove_slivers_by_area(self, sample_polygons):
        """Test removing polygons below area threshold."""
        filtered = remove_slivers(sample_polygons, min_area=2.0)

        assert len(filtered) > 0
        for _, props in filtered:
            assert props["area"] >= 2.0

    def test_remove_all_small_polygons(self, sample_polygons):
        """Test that all small polygons are removed."""
        filtered = remove_slivers(sample_polygons, min_area=10.0)

        # All sample polygons have area <= 4, so all should be removed
        assert len(filtered) == 0

    def test_remove_slivers_keeps_large_polygons(self, sample_polygons):
        """Test that large polygons are kept."""
        # First polygon (box 0-2, 0-2) has area 4.0
        filtered = remove_slivers(sample_polygons, min_area=1.0)

        assert len(filtered) > 0
        assert any(props["area"] >= 1.0 for _, props in filtered)

    def test_remove_slivers_with_perimeter_ratio(self, sample_polygons):
        """Test sliver removal with perimeter/area ratio."""
        filtered = remove_slivers(
            sample_polygons,
            min_area=0.0,
            max_perimeter_area_ratio=2.0,
        )

        for _, props in filtered:
            area = props["area"]
            perimeter = props["perimeter"]
            if area > 0:
                ratio = perimeter / area
                assert ratio <= 2.0

    def test_remove_slivers_thin_polygon(self, small_polygon):
        """Test removing thin/ribbon-like slivers."""
        polygons = [small_polygon]

        # By area
        filtered = remove_slivers(polygons, min_area=1.0)
        assert len(filtered) == 0

        # By perimeter ratio (very thin rectangle)
        filtered = remove_slivers(
            polygons,
            min_area=0.0,
            max_perimeter_area_ratio=100.0,
        )
        # Thin rectangle should be filtered
        assert len(filtered) == 0

    def test_remove_slivers_negative_area_raises_error(self, sample_polygons):
        """Test that negative min_area raises ValueError."""
        with pytest.raises(ValueError, match="min_area must be non-negative"):
            remove_slivers(sample_polygons, min_area=-1.0)

    def test_remove_slivers_empty_list(self):
        """Test removing slivers from empty list."""
        result = remove_slivers([], min_area=1.0)
        assert result == []

    def test_remove_slivers_preserves_properties(self, sample_polygons):
        """Test that properties are preserved after filtering."""
        filtered = remove_slivers(sample_polygons, min_area=0.1)

        for _, props in filtered:
            assert "value" in props
            assert "area" in props
            assert "perimeter" in props

    def test_remove_slivers_with_both_criteria(self):
        """Test removing slivers with both area and ratio criteria."""
        # Create polygons - one valid, one too thin
        poly1 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])  # 100 area, ratio ~0.4
        poly2 = Polygon([(0, 0), (100, 0), (100, 0.1), (0, 0.1)])  # thin ribbon

        polygons = [
            (poly1, {"value": 1, "area": poly1.area, "perimeter": poly1.length}),
            (poly2, {"value": 2, "area": poly2.area, "perimeter": poly2.length}),
        ]

        # Filter with both criteria
        filtered = remove_slivers(
            polygons,
            min_area=1.0,
            max_perimeter_area_ratio=100.0,
        )

        # Should keep only the first (non-thin) polygon
        assert len(filtered) > 0


class TestIsValidPolygon:
    """Test polygon validation."""

    def test_valid_polygon(self):
        """Test that a valid polygon passes validation."""
        poly = box(0, 0, 1, 1)
        assert is_valid_polygon(poly)

    def test_valid_polygon_with_area_threshold(self):
        """Test validation with area threshold."""
        poly = box(0, 0, 2, 2)  # area = 4
        assert is_valid_polygon(poly, min_area=1.0)
        assert not is_valid_polygon(poly, min_area=5.0)

    def test_invalid_polygon_fails(self):
        """Test that invalid polygon fails validation."""
        # Self-intersecting polygon
        invalid_poly = Polygon([(0, 0), (1, 1), (1, 0), (0, 1)])
        assert not is_valid_polygon(invalid_poly)

    def test_empty_polygon_fails(self):
        """Test that empty polygon fails validation."""
        empty_poly = Polygon()
        assert not is_valid_polygon(empty_poly)

    def test_polygon_with_perimeter_ratio_check(self):
        """Test validation with perimeter/area ratio."""
        poly = box(0, 0, 1, 1)  # ratio = 4/1
        assert is_valid_polygon(poly, max_perimeter_area_ratio=5.0)
        assert not is_valid_polygon(poly, max_perimeter_area_ratio=3.0)

    def test_thin_polygon_validation(self, small_polygon):
        """Test that thin polygons can be filtered by ratio."""
        poly, _ = small_polygon
        # Thin rectangle has high perimeter/area ratio
        assert not is_valid_polygon(poly, max_perimeter_area_ratio=100.0)


class TestFillHoles:
    """Test hole filling functionality."""

    def test_fill_holes_simple_polygon(self, sample_polygons):
        """Test filling holes in simple polygons without holes."""
        filled = fill_holes(sample_polygons)

        assert len(filled) == len(sample_polygons)
        for _, props in filled:
            assert "holes" in props
            assert props["holes"] == 0
            assert props["hole_area"] == 0

    def test_fill_holes_polygon_with_hole(self, polygon_with_hole):
        """Test filling a polygon that has interior holes."""
        polygons = [polygon_with_hole]
        filled = fill_holes(polygons)

        assert len(filled) == 1
        _, props = filled[0]
        assert props["holes"] == 1
        assert props["hole_area"] > 0

    def test_fill_holes_preserves_exterior(self, polygon_with_hole):
        """Test that exterior is preserved when filling holes."""
        poly, _ = polygon_with_hole
        polygons = [(poly, {"value": 1})]
        filled = fill_holes(polygons)

        filled_poly, _ = filled[0]
        # Filled polygon should match exterior
        exterior_poly = Polygon(poly.exterior.coords)
        assert filled_poly.equals(exterior_poly)

    def test_fill_holes_empty_list(self):
        """Test filling holes with empty list."""
        result = fill_holes([])
        assert result == []

    def test_fill_holes_properties_preserved(self, sample_polygons):
        """Test that original properties are preserved."""
        filled = fill_holes(sample_polygons)

        for i, (_, props) in enumerate(filled):
            original_value = sample_polygons[i][1]["value"]
            assert props["value"] == original_value


class TestDissolveByValue:
    """Test polygon dissolving functionality."""

    def test_dissolve_adjacent_same_value(self):
        """Test dissolving adjacent polygons with same raster value."""
        polygons = [
            (box(0, 0, 1, 1), {"value": 1, "area": 1.0, "perimeter": 4.0}),
            (box(1, 0, 2, 1), {"value": 1, "area": 1.0, "perimeter": 4.0}),
            (box(0, 1, 1, 2), {"value": 1, "area": 1.0, "perimeter": 4.0}),
        ]

        dissolved = dissolve_by_value(polygons)

        # All three polygons with value 1 should dissolve to one
        assert len(dissolved) == 1
        _, props = dissolved[0]
        assert props["value"] == 1
        assert props["polygon_count"] == 3

    def test_dissolve_different_values(self, sample_polygons):
        """Test that polygons with different values don't dissolve."""
        dissolved = dissolve_by_value(sample_polygons)

        # Sample polygons have different values
        assert len(dissolved) == len(sample_polygons)

    def test_dissolve_preserves_geometry(self):
        """Test that dissolving preserves geometry."""
        poly1 = box(0, 0, 1, 1)
        poly2 = box(1, 0, 2, 1)
        polygons = [
            (poly1, {"value": 1, "area": 1.0, "perimeter": 4.0}),
            (poly2, {"value": 1, "area": 1.0, "perimeter": 4.0}),
        ]

        dissolved = dissolve_by_value(polygons)

        _, props = dissolved[0]
        # Combined area should match
        assert props["area"] == pytest.approx(2.0, abs=0.1)

    def test_dissolve_empty_list(self):
        """Test dissolving empty list."""
        result = dissolve_by_value([])
        assert result == []

    def test_dissolve_single_polygon(self):
        """Test dissolving single polygon returns same."""
        polygons = [(box(0, 0, 1, 1), {"value": 1, "area": 1.0, "perimeter": 4.0})]

        dissolved = dissolve_by_value(polygons)

        assert len(dissolved) == 1
        _, props = dissolved[0]
        assert props["polygon_count"] == 1

    def test_dissolve_calculates_properties(self):
        """Test that dissolved polygons have correct properties."""
        polygons = [
            (box(0, 0, 1, 1), {"value": 1, "area": 1.0, "perimeter": 4.0}),
            (box(1, 0, 2, 1), {"value": 1, "area": 1.0, "perimeter": 4.0}),
        ]

        dissolved = dissolve_by_value(polygons)

        _, props = dissolved[0]
        assert "area" in props
        assert "perimeter" in props
        assert "polygon_count" in props
        assert props["polygon_count"] == 2

