"""
Polygon Hunter - AWS Lambda FastAPI Application

S3'teki gzip'li GeoJSON dosyalarını kullanarak
koordinatların hangi polygon içinde olduğunu bulan serverless API.
"""

from typing import List, Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse

from models import (
    Coordinate,
    BatchRequest,
    SearchResult,
    BatchResult,
    HealthResponse,
)
from services import (
    latlon_to_quadkey,
    find_polygons_containing_point,
)
from services.s3_client import get_s3_client


# FastAPI app
app = FastAPI(
    title="Polygon Hunter API",
    description="AWS Lambda + S3 based polygon search API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


def search_coordinate(lat: float, lon: float) -> SearchResult:
    """
    Search for polygons containing the given coordinate.
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        SearchResult with found polygons
    """
    s3_client = get_s3_client()
    
    # Calculate quadkey for zoom level 9
    quadkey = latlon_to_quadkey(lat, lon, zoom=9)
    
    # Check if quadkey exists in our data
    if not s3_client.has_quadkey(quadkey):
        return SearchResult(
            lat=lat,
            lon=lon,
            quadkey=quadkey,
            found=False,
            polygon_count=0,
            message=f"QuadKey {quadkey} not in coverage area"
        )
    
    # Get GeoJSON data from S3
    geojson = s3_client.get_geojson(quadkey)
    if not geojson:
        return SearchResult(
            lat=lat,
            lon=lon,
            quadkey=quadkey,
            found=False,
            polygon_count=0,
            message="Failed to load GeoJSON data"
        )
    
    # Find polygons containing the point
    matching_polygons = find_polygons_containing_point(geojson, lat, lon)
    
    return SearchResult(
        lat=lat,
        lon=lon,
        quadkey=quadkey,
        found=len(matching_polygons) > 0,
        polygon_count=len(matching_polygons),
        polygons=matching_polygons,
        message=None
    )


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint with S3 status."""
    s3_client = get_s3_client()
    stats = s3_client.get_stats()
    
    return HealthResponse(
        status="healthy",
        service="polygon-hunter-lambda",
        s3_bucket=stats["bucket"],
        total_quadkeys=stats["total_quadkeys"],
        total_polygons=stats["total_polygons"],
    )


@app.get("/search", response_model=SearchResult)
def search(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
):
    """
    Search for polygons containing a coordinate.
    
    Returns polygon data if the coordinate falls within any polygon.
    """
    return search_coordinate(lat, lon)


@app.post("/batch", response_model=BatchResult)
def batch_search(request: BatchRequest):
    """
    Search for polygons for multiple coordinates.
    
    Maximum 100 coordinates per request.
    """
    results = []
    with_polygons = 0
    without_polygons = 0
    
    for coord in request.coordinates:
        result = search_coordinate(coord.lat, coord.lon)
        results.append(result)
        
        if result.found:
            with_polygons += 1
        else:
            without_polygons += 1
    
    return BatchResult(
        results=results,
        total_coordinates=len(results),
        coordinates_with_polygons=with_polygons,
        coordinates_without_polygons=without_polygons,
    )


@app.get("/geojson")
def get_geojson(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
):
    """
    Get GeoJSON FeatureCollection for a coordinate.
    
    Returns polygons containing the point as a GeoJSON FeatureCollection.
    """
    result = search_coordinate(lat, lon)
    
    features = []
    for polygon in result.polygons:
        feature = {
            "type": "Feature",
            "geometry": polygon.get("geometry"),
            "properties": {
                **polygon.get("properties", {}),
                "search_point": {"lat": lat, "lon": lon},
                "quadkey": result.quadkey,
            }
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "query_point": {"lat": lat, "lon": lon},
            "quadkey": result.quadkey,
            "total_polygons": len(features),
        }
    }
    
    return JSONResponse(
        content=geojson,
        media_type="application/geo+json"
    )


@app.post("/batch-geojson")
def batch_geojson(request: BatchRequest):
    """
    Get GeoJSON FeatureCollection for multiple coordinates.
    
    Returns all matching polygons as a single GeoJSON FeatureCollection.
    """
    all_features = []
    
    for coord in request.coordinates:
        result = search_coordinate(coord.lat, coord.lon)
        
        for polygon in result.polygons:
            feature = {
                "type": "Feature",
                "geometry": polygon.get("geometry"),
                "properties": {
                    **polygon.get("properties", {}),
                    "search_point": {"lat": coord.lat, "lon": coord.lon},
                    "quadkey": result.quadkey,
                }
            }
            all_features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": all_features,
        "metadata": {
            "total_coordinates": len(request.coordinates),
            "total_polygons": len(all_features),
        }
    }
    
    return JSONResponse(
        content=geojson,
        media_type="application/geo+json"
    )


@app.get("/quadkeys")
def list_quadkeys():
    """List all available quadkeys."""
    s3_client = get_s3_client()
    return {
        "quadkeys": s3_client.get_all_quadkeys(),
        "total": len(s3_client.get_all_quadkeys()),
    }


@app.get("/stats")
def get_stats():
    """Get statistics about the polygon data."""
    s3_client = get_s3_client()
    return s3_client.get_stats()
