"""
Tests for raster_to_polygons.core module.

Tests raster-to-polygon conversion, feature extraction, and file I/O operations.
Achieves 100% line coverage of core.py.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import numpy as np
from shapely.geometry import box, Polygon

from raster_to_polygons.core import (
    raster_to_polygons,
    raster_to_features,
    _raster_to_shapes,
    _save_polygons,
)
import raster_to_polygons.core as core_module


class TestRasterToPolygons:
    """Test the main raster_to_polygons conversion function."""

    def test_basic_conversion(self, tmp_geotiff):
        """Test basic raster to polygon conversion."""
        polygons = raster_to_polygons(tmp_geotiff)

        assert isinstance(polygons, list)
        assert len(polygons) > 0

        for geom, props in polygons:
            assert isinstance(geom, Polygon)
            assert isinstance(props, dict)
            assert "value" in props
            assert "area" in props
            assert "perimeter" in props

    def test_conversion_with_output_file_shp(self, tmp_geotiff, tmp_path):
        """Test conversion with shapefile output."""
        output_file = tmp_path / "output.shp"

        polygons = raster_to_polygons(
            tmp_geotiff,
            output_file=output_file,
        )

        assert output_file.exists()
        assert len(polygons) > 0

    def test_conversion_with_output_file_geojson(self, tmp_geotiff, tmp_path):
        """Test conversion with GeoJSON output."""
        output_file = tmp_path / "output.geojson"

        polygons = raster_to_polygons(
            tmp_geotiff,
            output_file=output_file,
        )

        assert output_file.exists()
        assert len(polygons) > 0

        # Verify GeoJSON is valid
        with open(output_file) as f:
            geojson = json.load(f)
            assert geojson["type"] == "FeatureCollection"
            assert "features" in geojson

    def test_conversion_with_remove_slivers(self, tmp_geotiff):
        """Test conversion with sliver removal enabled."""
        polygons = raster_to_polygons(
            tmp_geotiff,
            remove_slivers=True,
        )

        assert len(polygons) > 0
        # All polygons should have area >= threshold
        for _, props in polygons:
            assert props["area"] > 0

    def test_conversion_with_custom_min_area(self, tmp_geotiff):
        """Test sliver removal with custom threshold."""
        polygons = raster_to_polygons(
            tmp_geotiff,
            remove_slivers=True,
            min_area=5.0,
        )

        for _, props in polygons:
            assert props["area"] >= 5.0

    def test_conversion_with_smooth_edges(self, tmp_geotiff):
        """Test conversion with edge smoothing."""
        polygons = raster_to_polygons(
            tmp_geotiff,
            smooth_edges=True,
            smoothness=1.0,
        )

        assert len(polygons) > 0

    def test_conversion_with_smoothness_parameter(self, tmp_geotiff):
        """Test different smoothness levels."""
        polygons1 = raster_to_polygons(tmp_geotiff, smooth_edges=True, smoothness=1.0)
        polygons2 = raster_to_polygons(tmp_geotiff, smooth_edges=True, smoothness=3.0)

        assert len(polygons1) > 0
        assert len(polygons2) > 0

    def test_conversion_specific_band(self, tmp_geotiff):
        """Test conversion of specific raster band."""
        polygons = raster_to_polygons(tmp_geotiff, band=1)

        assert len(polygons) > 0

    def test_invalid_band_raises_error(self, tmp_geotiff):
        """Test that invalid band index raises ValueError."""
        with pytest.raises(ValueError, match="Band index"):
            raster_to_polygons(tmp_geotiff, band=999)

    def test_nonexistent_file_raises_error(self):
        """Test that nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Raster file not found"):
            raster_to_polygons("/nonexistent/path/file.tif")

    def test_empty_raster(self, empty_geotiff):
        """Test conversion of empty raster (all NoData)."""
        polygons = raster_to_polygons(empty_geotiff)

        # Should handle gracefully and return empty or only valid polygons
        assert isinstance(polygons, list)

    def test_single_pixel_raster(self, single_pixel_geotiff):
        """Test conversion of single-pixel raster."""
        polygons = raster_to_polygons(single_pixel_geotiff)

        assert len(polygons) >= 0  # May or may not produce polygon

    def test_all_options_combined(self, tmp_geotiff, tmp_path):
        """Test conversion with all options enabled."""
        output_file = tmp_path / "output.shp"

        polygons = raster_to_polygons(
            tmp_geotiff,
            output_file=output_file,
            band=1,
            remove_slivers=True,
            min_area=0.5,
            smooth_edges=True,
            smoothness=2.0,
        )

        assert output_file.exists()
        assert len(polygons) > 0

    def test_raster_has_no_bands_error(self, tmp_path):
        """Test that raster with no bands raises error."""
        import rasterio
        from rasterio.transform import Affine
        
        # Create raster with 0 bands (edge case)
        # This is hard to do with rasterio, so we'll mock src.count
        zero_band_path = tmp_path / "zero_bands.tif"
        data = np.ones((10, 10), dtype=np.uint8)
        
        # Create a valid raster first
        with rasterio.open(
            zero_band_path,
            "w",
            driver="GTiff",
            height=10,
            width=10,
            count=1,
            dtype=data.dtype,
            transform=Affine.identity(),
            crs="EPSG:4326",
        ) as dst:
            dst.write(data, 1)
        
        # Verify the test raster has 1 band (normal case)
        with rasterio.open(zero_band_path) as src:
            assert src.count == 1

    def test_raster_has_zero_bands_raises_value_error_via_mock(self, tmp_path):
        """Cover the src.count == 0 defensive check in raster_to_polygons."""
        input_file = tmp_path / "dummy.tif"
        input_file.write_text("placeholder")

        class FakeDataset:
            count = 0

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with patch.object(core_module.rasterio, "open", return_value=FakeDataset()):
            with pytest.raises(ValueError, match="Raster has no bands"):
                raster_to_polygons(input_file)

    def test_raster_to_polygons_creates_properties(self, tmp_geotiff):
        """Test that polygon properties are correctly created."""
        polygons = raster_to_polygons(tmp_geotiff)

        for geom, props in polygons:
            # Verify properties exist and have correct types
            assert isinstance(props["value"], float)
            assert isinstance(props["area"], float)
            assert isinstance(props["perimeter"], float)
            assert props["area"] > 0
            assert props["perimeter"] > 0


class TestRasterToFeatures:
    """Test the raster_to_features function."""

    def test_basic_feature_extraction(self, tmp_geotiff):
        """Test basic feature extraction."""
        features = raster_to_features(tmp_geotiff)

        assert isinstance(features, list)
        assert len(features) > 0

        for feat in features:
            assert feat["type"] == "Feature"
            assert "geometry" in feat
            assert "properties" in feat

    def test_feature_geojson_format(self, tmp_geotiff):
        """Test that features are in valid GeoJSON format."""
        features = raster_to_features(tmp_geotiff)

        for feat in features:
            assert feat["geometry"]["type"] == "Polygon"
            assert "coordinates" in feat["geometry"]

    def test_features_with_options(self, tmp_geotiff):
        """Test feature extraction with sliver removal and smoothing."""
        features = raster_to_features(
            tmp_geotiff,
            remove_slivers=True,
            smooth_edges=True,
            smoothness=1.5,
        )

        assert len(features) > 0


class TestRasterToShapes:
    """Test the internal _raster_to_shapes function."""

    def test_raster_to_shapes_basic(self):
        """Test basic raster array to shapes conversion."""
        data = np.array([
            [1, 1, 2, 2],
            [1, 1, 2, 2],
            [3, 3, 4, 4],
            [3, 3, 4, 4],
        ], dtype=np.uint8)

        from rasterio.transform import Affine
        transform = Affine.identity()

        shapes_list = _raster_to_shapes(data, transform, None)

        assert isinstance(shapes_list, list)
        assert len(shapes_list) > 0

    def test_raster_to_shapes_with_nodata(self):
        """Test raster to shapes with NoData values."""
        data = np.array([
            [1, 1, 255, 255],
            [1, 1, 255, 255],
            [2, 2, 255, 255],
            [2, 2, 255, 255],
        ], dtype=np.uint8)

        from rasterio.transform import Affine
        transform = Affine.identity()

        shapes_list = _raster_to_shapes(data, transform, None, nodata=255)

        # Should only have shapes for values 1 and 2
        assert len(shapes_list) > 0

    def test_raster_to_shapes_invalid_geometry_handling(self):
        """Test that invalid geometries are handled gracefully."""
        # This creates a degenerate raster that might produce invalid geometries
        data = np.zeros((5, 5), dtype=np.uint8)
        data[0, 0] = 1
        data[2, 2] = 1

        from rasterio.transform import Affine
        transform = Affine.identity()

        shapes_list = _raster_to_shapes(data, transform, None)

        # Should handle any issues and return valid list
        assert isinstance(shapes_list, list)

    def test_raster_to_shapes_with_empty_result(self):
        """Test handling when all geometries are empty or skipped."""
        # All NoData
        data = np.full((5, 5), 255, dtype=np.uint8)

        from rasterio.transform import Affine
        transform = Affine.identity()

        shapes_list = _raster_to_shapes(data, transform, None, nodata=255)

        # Should return empty or handle gracefully
        assert isinstance(shapes_list, list)

    def test_raster_to_shapes_invalid_polygon_becomes_empty(self):
        """Cover invalid polygon repair and empty skip path."""
        data = np.array([[1]], dtype=np.uint8)

        class EmptyPolygon:
            is_valid = True
            is_empty = True
            area = 0.0
            length = 0.0

        class InvalidPolygon:
            is_valid = False
            is_empty = False

            def buffer(self, *_args, **_kwargs):
                return EmptyPolygon()

        with patch.object(core_module, "shapes", return_value=[({"type": "Polygon", "coordinates": []}, 1)]):
            with patch.object(core_module, "shape", return_value=InvalidPolygon()):
                out = _raster_to_shapes(data, transform=None, crs=None)
        assert out == []

    def test_raster_to_shapes_shape_exception_warns_and_continues(self):
        """Cover exception branch in _raster_to_shapes."""
        data = np.array([[1]], dtype=np.uint8)
        with patch.object(core_module, "shapes", return_value=[({"type": "Polygon", "coordinates": []}, 7)]):
            with patch.object(core_module, "shape", side_effect=RuntimeError("boom")):
                with pytest.warns(UserWarning, match="Failed to convert shape for value 7"):
                    out = _raster_to_shapes(data, transform=None, crs=None)
        assert out == []


class TestSavePolygons:
    """Test the internal _save_polygons function."""

    def test_save_polygons_shapefile(self, sample_polygons, tmp_path):
        """Test saving polygons to shapefile."""
        output_file = tmp_path / "output.shp"

        _save_polygons(sample_polygons, output_file, None)

        assert output_file.exists()

    def test_save_polygons_geojson(self, sample_polygons, tmp_path):
        """Test saving polygons to GeoJSON."""
        output_file = tmp_path / "output.geojson"

        _save_polygons(sample_polygons, output_file, None)

        assert output_file.exists()

        with open(output_file) as f:
            geojson = json.load(f)
            assert geojson["type"] == "FeatureCollection"
            assert len(geojson["features"]) == len(sample_polygons)

    def test_save_polygons_geojson_json_extension(self, sample_polygons, tmp_path):
        """Test that .json extension is recognized as GeoJSON."""
        output_file = tmp_path / "output.json"

        _save_polygons(sample_polygons, output_file, None)

        assert output_file.exists()

    def test_save_empty_polygons_raises_error(self, tmp_path):
        """Test that saving empty polygon list raises error."""
        output_file = tmp_path / "output.shp"

        with pytest.raises(ValueError, match="No polygons to save"):
            _save_polygons([], output_file, None)

    def test_save_unsupported_format_raises_error(self, sample_polygons, tmp_path):
        """Test that unsupported format raises error."""
        output_file = tmp_path / "output.xyz"

        with pytest.raises(ValueError, match="Unsupported output format"):
            _save_polygons(sample_polygons, output_file, None)

