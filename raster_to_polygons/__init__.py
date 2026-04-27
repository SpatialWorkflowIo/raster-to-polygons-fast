"""
raster-to-polygons-fast: Convert raster images to clean vector polygons.

Fast, clean GIS raster-to-vector conversion with sliver removal and optional smoothing.
"""

__version__ = "0.1.0"
__author__ = "Spatial Workflow"
__email__ = "info@spatialworkflow.io"
__license__ = "MIT"

from raster_to_polygons.core import raster_to_polygons

__all__ = ["raster_to_polygons", "__version__"]

