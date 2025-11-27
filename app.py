"""
FastAPI REST API for Polygon Hunter.

Production-ready REST endpoints for polygon search functionality.
"""

from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from models import Point, SearchResult
from api import PolygonHunterAPI
from utils import configure_logging

configure_logging()

# Initialize API with relative paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data2"
CSV_PATH = BASE_DIR / "polygon_counts_summary2.csv"

app = FastAPI(
    title="Polygon Hunter API",
    description="Find polygons containing given geographic coordinates. Returns polygon geometries in GeoJSON format.",
    version="1.0.0",
)

api = PolygonHunterAPI(DATA_DIR, CSV_PATH, zoom_level=9)


# Request/Response Models
class BatchCoordinateRequest(BaseModel):
    """Request model for batch coordinate search."""

    coordinates: List[Tuple[float, float]]

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates_list(cls, v):
        """Validate coordinate list."""
        if len(v) > 100:
            raise ValueError("Maximum 100 coordinates per request")
        return v


class PolygonResponse(BaseModel):
    """Polygon feature response."""

    type: str
    geometry: dict
    properties: dict


class SearchResponse(BaseModel):
    """Response model for polygon search."""

    status: str
    message: str
    quadkey: str
    file: str
    point: dict
    count: int
    polygons: List[PolygonResponse]


class QuadKeyInfoResponse(BaseModel):
    """Response model for QuadKey information."""

    quadkey: str
    zoom: int
    bounding_box: dict
    file: str
    file_exists: bool


# Routes
@app.get("/", tags=["info"])
async def root():
    """API root endpoint with documentation."""
    return {
        "name": "Polygon Hunter API",
        "version": "1.0.0",
        "description": "Find polygons containing geographic coordinates",
        "endpoints": {
            "search": "GET /search?lat=<latitude>&lon=<longitude>",
            "geojson": "GET /geojson?lat=<latitude>&lon=<longitude>",
            "batch": "POST /batch",
            "batch-geojson": "POST /batch-geojson",
            "quadkey-info": "GET /quadkey-info/<quadkey>",
            "health": "GET /health",
        },
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "quadkeys_indexed": api.index.count(),
        "data_dir": str(api.data_dir),
    }


@app.get("/geojson", tags=["geojson"])
async def get_geojson(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
):
    """
    Get polygons as GeoJSON FeatureCollection for a single coordinate.

    Returns a valid GeoJSON FeatureCollection containing all matching polygons.

    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)

    Returns:
        GeoJSON FeatureCollection

    Example:
        /geojson?lat=40.9887&lon=29.0252
    """
    try:
        point = Point(lat, lon)
        result = api.find_polygons(point)

        features = []
        for polygon in result.polygons:
            feature = {
                "type": "Feature",
                "geometry": polygon["geometry"],
                "properties": {
                    **polygon.get("properties", {}).get("properties", {}),
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
                "generated_at": datetime.now().isoformat()
            }
        }

        return JSONResponse(content=geojson, media_type="application/geo+json")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/search", response_model=SearchResponse, tags=["search"])
async def search_polygons(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
):
    """
    Find all polygons containing the given coordinate.

    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)

    Returns:
        List of polygons containing the point

    Example:
        /search?lat=40.9887&lon=29.0252
    """
    try:
        point = Point(lat, lon)
        result = api.find_polygons(point)

        return SearchResponse(
            status=result.status,
            message=result.message,
            quadkey=result.quadkey,
            file=result.file or "",
            point=result.point or {},
            count=result.count,
            polygons=[
                PolygonResponse(
                    type=p["type"],
                    geometry=p["geometry"],
                    properties=p["properties"],
                )
                for p in result.polygons
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/batch", response_model=List[SearchResponse], tags=["search"])
async def batch_search(request: BatchCoordinateRequest):
    """
    Find polygons for multiple coordinates in batch.

    Args:
        coordinates: List of [lat, lon] pairs

    Returns:
        List of search results

    Example:
        POST /batch
        {"coordinates": [[40.9887, 29.0252], [41.0330, 26.7188]]}
    """
    try:
        results = api.find_polygons_batch(request.coordinates)

        return [
            SearchResponse(
                status=r.status,
                message=r.message,
                quadkey=r.quadkey or "",
                file=r.file or "",
                point=r.point or {},
                count=r.count,
                polygons=[
                    PolygonResponse(
                        type=p["type"],
                        geometry=p["geometry"],
                        properties=p["properties"],
                    )
                    for p in r.polygons
                ],
            )
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/batch-geojson", tags=["geojson"])
async def batch_geojson(request: BatchCoordinateRequest):
    """
    Get polygons as GeoJSON FeatureCollection for multiple coordinates.

    Returns a valid GeoJSON FeatureCollection containing all matching polygons
    for all coordinates, plus Point features for coordinates without matches.

    Args:
        coordinates: List of [lat, lon] pairs

    Returns:
        GeoJSON FeatureCollection

    Example:
        POST /batch-geojson
        {"coordinates": [[40.9887, 29.0252], [41.0330, 26.7188]]}
    """
    try:
        results = api.find_polygons_batch(request.coordinates)
        
        features = []
        points_with_polygon = 0
        points_without_polygon = 0
        
        for i, result in enumerate(results):
            coord = request.coordinates[i]
            lat, lon = coord[0], coord[1]
            
            if result.polygons:
                points_with_polygon += 1
                # Add polygon features
                for poly_idx, polygon in enumerate(result.polygons):
                    feature = {
                        "type": "Feature",
                        "geometry": polygon["geometry"],
                        "properties": {
                            **polygon.get("properties", {}).get("properties", {}),
                            "feature_type": "matched_polygon",
                            "search_point": {"lat": lat, "lon": lon},
                            "quadkey": result.quadkey,
                            "point_index": i + 1,
                            "polygon_index": poly_idx + 1
                        }
                    }
                    features.append(feature)
            else:
                points_without_polygon += 1
                # Add point feature for no match
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    },
                    "properties": {
                        "feature_type": "no_polygon_found",
                        "search_point": {"lat": lat, "lon": lon},
                        "quadkey": result.quadkey,
                        "point_index": i + 1,
                        "status": result.status,
                        "message": result.message
                    }
                }
                features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "total_search_points": len(request.coordinates),
                "points_with_polygon": points_with_polygon,
                "points_without_polygon": points_without_polygon,
                "total_features": len(features),
                "generated_at": datetime.now().isoformat()
            }
        }
        
        return JSONResponse(content=geojson, media_type="application/geo+json")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/quadkey-info/{quadkey}", response_model=QuadKeyInfoResponse, tags=["info"])
async def get_quadkey_info(quadkey: str):
    """
    Get information about a specific QuadKey tile.

    Args:
        quadkey: QuadKey string

    Returns:
        Information about the tile

    Example:
        /quadkey-info/120323223
    """
    try:
        if not quadkey.isdigit() or not all(c in "0123" for c in quadkey):
            raise ValueError("Invalid QuadKey format")

        info = api.get_quadkey_info(quadkey)

        return QuadKeyInfoResponse(
            quadkey=info.quadkey,
            zoom=info.zoom,
            bounding_box=info.bounding_box.to_dict(),
            file=info.file or "",
            file_exists=info.file_exists,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/available-quadkeys", tags=["info"])
async def list_quadkeys(limit: int = Query(50, ge=1, le=500)):
    """
    List available QuadKeys.

    Args:
        limit: Maximum number of QuadKeys to return

    Returns:
        List of available QuadKeys
    """
    quadkeys = api.index.list_all_quadkeys()
    return {
        "total": len(quadkeys),
        "limit": limit,
        "quadkeys": quadkeys[:limit],
    }


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    return HTTPException(status_code=400, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
