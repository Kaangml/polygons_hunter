"""
Pydantic models for AWS Lambda API.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Coordinate(BaseModel):
    """A geographic coordinate point."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")


class BatchRequest(BaseModel):
    """Request for batch coordinate search."""
    coordinates: List[Coordinate] = Field(..., min_length=1, max_length=100)


class PolygonResult(BaseModel):
    """Result for a single polygon match."""
    geometry: Dict[str, Any] = Field(..., description="GeoJSON geometry")
    properties: Dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """Result for a coordinate search."""
    lat: float
    lon: float
    quadkey: str
    found: bool
    polygon_count: int = 0
    polygons: List[Dict[str, Any]] = Field(default_factory=list)
    message: Optional[str] = None


class BatchResult(BaseModel):
    """Result for batch coordinate search."""
    results: List[SearchResult]
    total_coordinates: int
    coordinates_with_polygons: int
    coordinates_without_polygons: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    service: str = "polygon-hunter-lambda"
    s3_bucket: str
    total_quadkeys: int
    total_polygons: int


class GeoJSONFeature(BaseModel):
    """GeoJSON Feature."""
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any] = Field(default_factory=dict)


class GeoJSONFeatureCollection(BaseModel):
    """GeoJSON FeatureCollection."""
    type: str = "FeatureCollection"
    features: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
