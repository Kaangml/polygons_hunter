"""
Data models and type definitions.

This module contains all data classes and type hints used throughout
the Polygon Hunter application.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class Point:
    """Represents a geographic point with latitude and longitude."""

    lat: float
    lon: float

    def __post_init__(self):
        """Validate coordinates are within valid geographic ranges."""
        if not -90 <= self.lat <= 90:
            raise ValueError(f"Latitude must be in [-90, 90], got {self.lat}")
        if not -180 <= self.lon <= 180:
            raise ValueError(f"Longitude must be in [-180, 180], got {self.lon}")

    def to_dict(self) -> Dict[str, float]:
        """Convert point to dictionary."""
        return {"lat": self.lat, "lon": self.lon}


@dataclass
class BoundingBox:
    """Represents a geographic bounding box."""

    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float

    def contains_point(self, point: Point) -> bool:
        """Check if bounding box contains the point."""
        return (
            self.min_lat <= point.lat <= self.max_lat
            and self.min_lon <= point.lon <= self.max_lon
        )

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "min_lat": self.min_lat,
            "min_lon": self.min_lon,
            "max_lat": self.max_lat,
            "max_lon": self.max_lon,
        }


@dataclass
class Polygon:
    """Represents a polygon feature."""

    geometry: Dict[str, Any]
    properties: Dict[str, Any]

    def to_feature(self) -> Dict[str, Any]:
        """Convert to GeoJSON Feature format."""
        return {
            "type": "Feature",
            "geometry": self.geometry,
            "properties": self.properties,
        }


@dataclass
class SearchResult:
    """Result of a polygon search operation."""

    status: str  # "success" or "error"
    message: str
    quadkey: Optional[str]
    file: Optional[str]
    point: Optional[Dict[str, float]]
    polygons: List[Dict[str, Any]]
    count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "status": self.status,
            "message": self.message,
            "quadkey": self.quadkey,
            "file": self.file,
            "point": self.point,
            "polygons": self.polygons,
            "count": self.count,
        }


@dataclass
class QuadKeyInfo:
    """Information about a QuadKey tile."""

    quadkey: str
    zoom: int
    bounding_box: BoundingBox
    file: Optional[str]
    file_exists: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "quadkey": self.quadkey,
            "zoom": self.zoom,
            "bounding_box": self.bounding_box.to_dict(),
            "file": self.file,
            "file_exists": self.file_exists,
        }

