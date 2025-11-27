"""
Main API service - Polygon Hunter.

High-level API that coordinates all services to find polygons
containing given coordinates.
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from models import Point, SearchResult, QuadKeyInfo
from services.quadkey import QuadKeyConverter
from services.geometry import PointInPolygon
from services.index import QuadKeyIndex

logger = logging.getLogger(__name__)


class PolygonHunterAPI:
    """
    Main API for finding polygons containing given coordinates.

    This API coordinates multiple services:
    1. QuadKeyConverter: Converts coordinates to QuadKey
    2. QuadKeyIndex: Finds GeoJSON file for a QuadKey
    3. PointInPolygon: Detects if point is in polygon
    """

    def __init__(self, data_dir: Path, csv_path: Path, zoom_level: int = 9):
        """
        Initialize the API.

        Args:
            data_dir: Directory containing GeoJSON files
            csv_path: Path to the CSV index file
            zoom_level: Zoom level for QuadKey generation (default: 9)

        Raises:
            FileNotFoundError: If data directory or CSV doesn't exist
        """
        self.data_dir = Path(data_dir)
        self.csv_path = Path(csv_path)
        self.zoom_level = zoom_level

        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV index not found: {csv_path}")

        self.converter = QuadKeyConverter()
        self.index = QuadKeyIndex(self.csv_path)

        logger.info(
            f"PolygonHunterAPI initialized with zoom_level={zoom_level}, "
            f"index_size={self.index.count()}"
        )

    @lru_cache(maxsize=32)
    def _load_geojson(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load and cache GeoJSON file.

        LRU cache prevents repeated disk reads for the same file.

        Args:
            file_path: Path to GeoJSON file (relative to data_dir)

        Returns:
            Parsed GeoJSON data or None if loading fails
        """
        full_path = self.data_dir / file_path
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.debug(f"Loaded GeoJSON from {full_path}")
            return data
        except FileNotFoundError:
            logger.error(f"GeoJSON file not found: {full_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GeoJSON {full_path}: {e}")
            return None

    def _extract_matching_polygons(
        self, point: Point, geojson_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract all polygons from GeoJSON that contain the point.

        Args:
            point: Point to search for
            geojson_data: Parsed GeoJSON FeatureCollection

        Returns:
            List of matching polygon features
        """
        matching_polygons = []
        features = geojson_data.get("features", [])

        for feature in features:
            geometry = feature.get("geometry")
            if not geometry:
                continue

            if PointInPolygon.check_point_in_geometry(point, geometry):
                matching_polygons.append(
                    {
                        "type": "Feature",
                        "geometry": geometry,
                        "properties": feature.get("properties", {}),
                    }
                )

        return matching_polygons

    def find_polygons(self, point: Point) -> SearchResult:
        """
        Find all polygons that contain the given point.

        This is the main API method. It:
        1. Converts point to QuadKey
        2. Finds corresponding GeoJSON file
        3. Loads and searches file for containing polygons

        Args:
            point: Point to search for

        Returns:
            SearchResult with status, polygons found, and metadata

        Example:
            >>> api = PolygonHunterAPI(data_dir, csv_path)
            >>> point = Point(lat=40.9887, lon=29.0252)
            >>> result = api.find_polygons(point)
            >>> print(f"Found {result.count} polygons")
        """
        try:
            # Step 1: Convert to QuadKey
            quadkey = self.converter.latlon_to_quadkey(
                point.lat, point.lon, self.zoom_level
            )
            logger.info(
                f"Point ({point.lat}, {point.lon}) → QuadKey: {quadkey}"
            )

            # Step 2: Find corresponding file
            geojson_file = self.index.get_file_for_quadkey(quadkey)
            if not geojson_file:
                logger.warning(f"No GeoJSON file found for QuadKey: {quadkey}")
                return SearchResult(
                    status="error",
                    message=f"No data available for QuadKey {quadkey}",
                    quadkey=quadkey,
                    file=None,
                    point=point.to_dict(),
                    polygons=[],
                    count=0,
                )

            # Step 3: Load GeoJSON
            geojson_data = self._load_geojson(str(geojson_file))
            if not geojson_data:
                return SearchResult(
                    status="error",
                    message=f"Failed to load GeoJSON file: {geojson_file}",
                    quadkey=quadkey,
                    file=str(geojson_file),
                    point=point.to_dict(),
                    polygons=[],
                    count=0,
                )

            # Step 4: Search for containing polygons
            matching_polygons = self._extract_matching_polygons(
                point, geojson_data
            )

            logger.info(
                f"Found {len(matching_polygons)} polygons for "
                f"point ({point.lat}, {point.lon})"
            )

            return SearchResult(
                status="success",
                message=f"Found {len(matching_polygons)} polygons",
                quadkey=quadkey,
                file=str(geojson_file),
                point=point.to_dict(),
                polygons=matching_polygons,
                count=len(matching_polygons),
            )

        except ValueError as e:
            logger.error(f"Invalid input: {e}")
            return SearchResult(
                status="error",
                message=f"Invalid input: {str(e)}",
                quadkey=None,
                file=None,
                point=None,
                polygons=[],
                count=0,
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return SearchResult(
                status="error",
                message=f"Unexpected error: {str(e)}",
                quadkey=None,
                file=None,
                point=None,
                polygons=[],
                count=0,
            )

    def find_polygons_batch(
        self, points: List[Tuple[float, float]]
    ) -> List[SearchResult]:
        """
        Find polygons for multiple points.

        Args:
            points: List of (lat, lon) tuples

        Returns:
            List of SearchResult for each point
        """
        results = []
        for lat, lon in points:
            try:
                point = Point(lat, lon)
                result = self.find_polygons(point)
                results.append(result)
            except ValueError as e:
                logger.error(f"Invalid point ({lat}, {lon}): {e}")
                results.append(
                    SearchResult(
                        status="error",
                        message=f"Invalid point: {str(e)}",
                        quadkey=None,
                        file=None,
                        point={"lat": lat, "lon": lon},
                        polygons=[],
                        count=0,
                    )
                )

        return results

    def get_quadkey_info(self, quadkey: str) -> QuadKeyInfo:
        """
        Get information about a QuadKey tile.

        Args:
            quadkey: QuadKey string

        Returns:
            QuadKeyInfo with tile metadata and file information
        """
        bbox = self.converter.quadkey_to_bbox(quadkey)
        file_path = self.index.get_file_for_quadkey(quadkey)
        file_exists = (
            (self.data_dir / file_path).exists() if file_path else False
        )

        return QuadKeyInfo(
            quadkey=quadkey,
            zoom=len(quadkey),
            bounding_box=bbox,
            file=str(file_path) if file_path else None,
            file_exists=file_exists,
        )
