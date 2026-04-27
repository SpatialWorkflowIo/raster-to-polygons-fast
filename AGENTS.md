# AGENTS.md: raster-to-polygons-fast Development Guide

## Project Vision

This is a Python tool for converting raster images to clean vector polygon geometries. The focus is on:
- **Fast processing** using GDAL/rasterio
- **Clean boundaries** without artifacts
- **Sliver polygon removal** (small/invalid polygons)
- **Optional smoothing** of polygon edges

The tool should be beginner-friendly, well-documented, and production-ready with 100% test coverage.

## Author Requirements (Non-Negotiable)

These requirements from `description.md` must be met:
1. **100% test coverage** - every line of code must be tested
2. **Comprehensive README.md** with quickstart, examples, and beginner-friendly explanations
3. **Copy-paste quickstart commands** in docs for immediate usability
4. **Link to https://spatialworkflow.io/** in documentation as author's website
5. **Public GitHub repo** at github-spatial:spatialworkflowIo/raster-to-polygons-fast

## Project Structure

```
raster-to-polygons-fast/
├── README.md                 # Main documentation with examples & quickstart
├── raster_to_polygons/      # Main package
│   ├── __init__.py
│   ├── core.py              # Core rasterization logic (GDAL/rasterio)
│   ├── cleaner.py           # Sliver removal, boundary cleaning
│   ├── smoother.py          # Optional edge smoothing
│   └── cli.py               # Command-line interface
├── tests/                    # Must achieve 100% coverage
│   ├── test_core.py
│   ├── test_cleaner.py
│   ├── test_smoother.py
│   ├── fixtures/            # Sample raster files for testing
│   └── conftest.py          # Pytest fixtures
├── setup.py / pyproject.toml # Dependencies: gdal, rasterio, shapely, numpy
├── .github/workflows/        # CI/CD for test coverage reporting
└── examples/                 # Real-world usage examples with data
```

## Core Dependencies

- **rasterio** - preferred over raw GDAL bindings (more Pythonic)
- **shapely** - geometry manipulation and validation
- **numpy** - array operations
- **gdal** - underlying raster processing (installed via rasterio)
- **click** or **argparse** - CLI interface

## Key Workflows

### Development with 100% Coverage
```bash
pytest --cov=raster_to_polygons --cov-report=term-missing
```
Every PR must show 100% line coverage. Use `pytest-cov` as enforced dependency.

### Running Tests Locally
```bash
pip install -e ".[dev]"  # Install in dev mode with test dependencies
pytest -v
```

### CLI Interface Pattern
The tool should expose:
```bash
raster-to-polygons input.tif output.shp [--remove-slivers --smooth]
```
Keep CLI simple and discoverable via `--help`.

## Code Patterns & Conventions

### 1. GIS Data Handling
- Always work with **CRS (Coordinate Reference System)** explicitly
- Use rasterio's context managers: `with rasterio.open(path) as src:`
- Validate geometries with `shapely.geometry.shape()` validation
- Test edge cases: empty rasters, single-pixel features, CRS mismatches

### 2. Sliver Removal Pattern
Example approach:
```python
# Remove polygons below area threshold or with high perimeter/area ratio
for polygon in geometries:
    area = polygon.area
    if area < min_area_threshold:
        continue  # Skip sliver
```
Must be configurable (allow users to set threshold).

### 3. Documentation First
- **Every function** must have a docstring with:
  - One-line summary
  - Args (with types)
  - Returns (with types)
  - Example: `>>> raster_to_polygons('input.tif', output='output.shp')`
- Use `sphinx` for API documentation generation

### 4. Testing Pattern: Fixtures Over Mock
- Create small sample GeoTIFF files in `tests/fixtures/`
- Use real raster files in tests, not mocks
- Example fixture:
  ```python
  @pytest.fixture
  def sample_geotiff(tmp_path):
      # Create minimal test raster with known geometry
  ```

### 5. Error Handling
Raise descriptive errors early:
```python
if not Path(input_file).exists():
    raise FileNotFoundError(f"Raster file not found: {input_file}")
if src.count == 0:
    raise ValueError("Raster has no bands")
```

## README.md Structure (Required)

1. **Elevator pitch** (1 sentence)
2. **Features** (bullet list with why each matters)
3. **Installation** (platform-specific for GDAL complexity)
4. **Quickstart** (copy-paste example with sample data)
5. **API Reference** (link to generated Sphinx docs)
6. **Examples** (2-3 real-world use cases with before/after)
7. **Performance** (runtime expectations, file size limits)
8. **License & Author** (link to https://spatialworkflow.io/)

### Required README Examples
Include literal example:
```bash
# Download sample (or ship with repo)
wget https://example.com/sample.tif
raster-to-polygons sample.tif output.shp --remove-slivers
```

## Testing Strategy for 100% Coverage

1. **Unit tests** - test each function in isolation with fixtures
2. **Integration tests** - test pipeline end-to-end
3. **Edge case tests**:
   - Empty raster (all NoData)
   - Single pixel raster
   - Large files (performance check)
   - Different CRS systems
   - Floating-point rasters vs integer
4. **Snapshot tests** - compare output geometries against known-good results

Use `pytest-cov` to verify coverage after every change.

## GitHub Setup

- Use **SSH key**: `~/.ssh/id_ed25519_spatialworkflow` configured as `github-spatial`
- Commit messages: Reference what was built/fixed (e.g., "Add sliver removal with 5m² threshold")
- Make repo **public** from the start
- Initialize with this repo as base

## Performance Expectations

Document in README:
- Typical processing time for common source raster sizes
- Memory usage for large files
- Known limitations (e.g., "best for geotiffs under 1GB")

---

**For AI Agents**: Always start with tests before implementation. Write failing tests for the feature, then implement to pass them. This ensures 100% coverage naturally.

