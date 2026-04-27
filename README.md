# raster-to-polygons-fast

**Fast, clean GIS raster-to-vector conversion with sliver removal and optional edge smoothing.**

Convert satellite imagery, drone data, and other raster formats into clean vector polygons—automatically removing small artifacts and smoothing jagged boundaries.

<img alt="Raster to Polygon Conversion" src="https://via.placeholder.com/600x300?text=Raster+to+Polygons+Conversion" />

---

## ✨ Features

- **🚀 Fast Processing** - Uses `rasterio` and GDAL for optimized raster I/O
- **🎯 Clean Boundaries** - Removes rasterization artifacts and jagged edges
- **🗑️ Sliver Removal** - Automatically filters small/invalid polygons
- **✨ Optional Smoothing** - Chaikin's algorithm for beautiful edges
- **📁 Multiple Formats** - GeoTIFF, JPEG2000, and more (anything rasterio reads)
- **💾 Flexible Output** - Shapefile, GeoJSON, or in-memory geometries
- **🐍 Beginner-Friendly** - Simple Python API, intuitive CLI
- **✅ 100% Tested** - Production-ready with full test coverage

---

## 📦 Installation

### Prerequisites

Ensure you have Python 3.8+ and GDAL libraries installed on your system:

**Ubuntu/Debian:**
```bash
sudo apt-get install gdal-bin libgdal-dev
```

**macOS (with Homebrew):**
```bash
brew install gdal
```

**Windows:**
Download from [OSGeo4W](https://trac.osgeo.org/osgeo4w/) or use conda (recommended)

### Install Package

```bash
pip install raster-to-polygons-fast
```

Or for development:
```bash
git clone https://github.com/spatialworkflowIo/raster-to-polygons-fast.git
cd raster-to-polygons-fast
pip install -e ".[dev]"
```

---

## 🚀 Quickstart

### Command-Line Usage

Convert a raster to shapefile with automatic sliver removal and smoothing:

```bash
# Basic conversion
raster-to-polygons input.tif output.shp

# Remove slivers and smooth edges
raster-to-polygons input.tif output.shp --remove-slivers --smooth

# Custom minimum area (50 m²) and smoothness (heavy)
raster-to-polygons input.tif output.shp \
  --remove-slivers --min-area 50 \
  --smooth --smoothness 3.0

# Save as GeoJSON instead
raster-to-polygons input.tif output.geojson --remove-slivers
```

### Python API

```python
from raster_to_polygons import raster_to_polygons

# Simple conversion
polygons = raster_to_polygons('input.tif', output_file='output.shp')

# With all options
polygons = raster_to_polygons(
    'input.tif',
    output_file='output.shp',
    band=1,                    # Which band to convert
    remove_slivers=True,       # Filter small polygons
    min_area=5.0,              # Minimum area in map units
    smooth_edges=True,         # Smooth boundaries
    smoothness=1.5,            # 1.0 = light, 3.0 = heavy
)

# In-memory geometries (no file output)
from raster_to_polygons import raster_to_features

features = raster_to_features('input.tif', remove_slivers=True)
for feature in features:
    print(feature['geometry'])  # Shapely-compatible geometry
    print(feature['properties'])  # {'value': ..., 'area': ..., 'perimeter': ...}
```

---

## 📚 API Reference

### Main Functions

#### `raster_to_polygons()`

Convert raster to vector polygons with optional cleaning and smoothing.

**Parameters:**
- `input_file` (str/Path): Input raster file path
- `output_file` (str/Path, optional): Output shapefile or GeoJSON path
- `band` (int): Raster band index (1-indexed, default: 1)
- `remove_slivers` (bool): Remove small polygons (default: False)
- `min_area` (float, optional): Minimum polygon area. Auto-calculated if None
- `smooth_edges` (bool): Apply edge smoothing (default: False)
- `smoothness` (float): Smoothing intensity, 1.0–3.0 (default: 1.0)

**Returns:**
List of `(Polygon, properties_dict)` tuples

**Example:**
```python
from raster_to_polygons import raster_to_polygons

polygons = raster_to_polygons(
    'satellite.tif',
    output_file='output.shp',
    remove_slivers=True,
    smooth_edges=True
)
print(f"Created {len(polygons)} polygons")
```

#### `raster_to_features()`

Convert raster to GeoJSON-like features.

**Returns:**
List of GeoJSON Feature dicts with `geometry` and `properties`

**Example:**
```python
from raster_to_polygons import raster_to_features
import json

features = raster_to_features('input.tif')
geojson = {
    "type": "FeatureCollection",
    "features": features
}
print(json.dumps(geojson))
```

### Cleaning Functions

See `raster_to_polygons.cleaner` module:

- `remove_slivers()` - Filter polygons by area and shape metrics
- `is_valid_polygon()` - Validate polygon geometry
- `fill_holes()` - Remove interior holes from polygons
- `dissolve_by_value()` - Merge adjacent polygons with same raster value

### Smoothing Functions

See `raster_to_polygons.smoother` module:

- `smooth_geometries()` - Apply Chaikin smoothing to polygons
- `simplify_geometries()` - Reduce coordinate count via Douglas-Peucker
- `chaikin_smooth()` - Direct Chaikin algorithm application

For full API documentation:
```bash
# Generate Sphinx HTML docs
pip install sphinx sphinx-rtd-theme
cd docs
make html
open _build/html/index.html
```

---

## 💡 Examples

### Example 1: Satellite Image Classification

Convert classified satellite imagery (e.g., NDVI classes) to vector polygons:

```python
from raster_to_polygons import raster_to_polygons

# NDVI classification: 1=low vegetation, 2=medium, 3=high
polygons = raster_to_polygons(
    'ndvi_classified.tif',
    output_file='vegetation_zones.shp',
    remove_slivers=True,      # Remove noise pixels
    min_area=100.0,           # Only zones > 100 m²
    smooth_edges=True         # Professional boundaries
)

# Analyze results
for geom, props in polygons:
    value = props['value']
    area = props['area']
    print(f"Vegetation class {value}: {area:.1f} m²")
```

### Example 2: Drone Orthomosaic Segmentation

Segment drone data to extract building footprints:

```python
from raster_to_polygons import raster_to_polygons, raster_to_features
import json

# Binary classification: 0=background, 1=building
features = raster_to_features(
    'drone_orthomosaic.tif',
    remove_slivers=True,
    min_area=20.0,            # Only buildings > 20 m²
    smooth_edges=True
)

# Export as GeoJSON for web mapping
geojson = {
    "type": "FeatureCollection",
    "features": [f for f in features if f['properties']['value'] == 1]
}

with open('buildings.geojson', 'w') as f:
    json.dump(geojson, f, indent=2)

print(f"Extracted {len(geojson['features'])} buildings")
```

### Example 3: Multi-Band Processing

Process specific bands from multi-band imagery:

```python
from raster_to_polygons import raster_to_polygons

# Extract Band 2 (Red) from Landsat TIFF
polygons = raster_to_polygons(
    'landsat_8.tif',
    band=2,                   # Select band 2
    output_file='red_zones.shp',
    remove_slivers=True
)
```

---

## ⚙️ Performance

Processing time and memory usage vary by raster size:

| Raster Size | Typical Time | Memory Usage | Notes |
|------------|-------------|--------------|-------|
| 1 km² (1000x1000 px) | 0.5–2 sec | ~50 MB | Typical drone orthomosaic |
| 10 km² (3162x3162 px) | 5–15 sec | ~200 MB | Medium satellite scene |
| 100 km² (10000x10000 px) | 30–120 sec | ~1 GB | Large satellite scene |
| > 1 GB files | **Not recommended** | > 4 GB | Consider tiling |

**Tips for Large Files:**
- Tile rasters before processing (`gdal_translate -co TILED=YES`)
- Process by band for multi-band files
- Disable smoothing initially (`--smooth` adds ~10% overhead)
- Use appropriate `--min-area` threshold to reduce polygon count

**Tested Platforms:**
- ✅ Linux (Ubuntu 20.04+)
- ✅ macOS (10.15+)
- ✅ Windows 10+ (via conda-forge rasterio)

---

## 🔧 Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests with coverage
pytest --cov=raster_to_polygons --cov-report=term-missing

# Run specific test file
pytest tests/test_core.py -v

# Run with detailed output
pytest -vv --tb=short
```

Expected output: **100% test coverage**

### Building Documentation

```bash
pip install sphinx sphinx-rtd-theme
cd docs
make html
open _build/html/index.html
```

### Code Style

```bash
# Format code
black raster_to_polygons/ tests/

# Lint
flake8 raster_to_polygons/ tests/

# Type checking
mypy raster_to_polygons/
```

---

## 📄 License

MIT License - See LICENSE file for details

**Author:** [Spatial Workflow](https://spatialworkflow.io/)

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for any new functionality (must maintain 100% coverage)
4. Commit with descriptive messages (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

---

## 🐛 Issues & Feedback

- **Bug Reports:** [GitHub Issues](https://github.com/spatialworkflowIo/raster-to-polygons-fast/issues)
- **Feature Requests:** Discussion in Issues welcome
- **Questions:** See [Spatial Workflow](https://spatialworkflow.io/) for contact info

---

## 📚 Related Projects

- [GDAL](https://gdal.org/) - Geospatial Data Abstraction Library
- [rasterio](https://rasterio.readthedocs.io/) - Pythonic GDAL bindings
- [Shapely](https://shapely.readthedocs.io/) - Geometric operations
- [PyGEOS](https://pygeos.readthedocs.io/) - Fast geometry operations (optional)

---

*Made with ❤️ for the GIS community. Visit [spatialworkflow.io](https://spatialworkflow.io/) for more tools.*

