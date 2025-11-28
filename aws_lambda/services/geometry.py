"""
AWS Lambda için Point-in-Polygon detection service.

Ray casting algoritması ile bir noktanın polygon içinde olup olmadığını kontrol eder.
"""

from typing import List, Tuple


def is_point_in_polygon(lat: float, lon: float, polygon_coords: List[List[float]]) -> bool:
    """
    Check if a point is inside a polygon using the ray casting algorithm.
    
    Args:
        lat: Latitude of the point
        lon: Longitude of the point
        polygon_coords: List of [lon, lat] coordinates forming the polygon ring
    
    Returns:
        True if point is inside polygon, False otherwise
    """
    if len(polygon_coords) < 3:
        return False

    x, y = lon, lat
    n = len(polygon_coords)
    inside = False

    j = n - 1
    for i in range(n):
        xi, yi = polygon_coords[i][0], polygon_coords[i][1]
        xj, yj = polygon_coords[j][0], polygon_coords[j][1]

        # Check if ray crosses edge
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside

        j = i

    return inside


def is_point_in_multipolygon(lat: float, lon: float, multipolygon_coords: List) -> bool:
    """
    Check if a point is inside any polygon in a multipolygon.
    
    Args:
        lat: Latitude of the point
        lon: Longitude of the point
        multipolygon_coords: List of polygons
    
    Returns:
        True if point is inside any polygon
    """
    for polygon in multipolygon_coords:
        if polygon and is_point_in_polygon(lat, lon, polygon[0]):
            return True
    return False


def check_point_in_geometry(lat: float, lon: float, geometry: dict) -> bool:
    """
    Check if point is in a GeoJSON geometry object.
    
    Args:
        lat: Latitude of the point
        lon: Longitude of the point
        geometry: GeoJSON geometry object
    
    Returns:
        True if point is inside geometry
    """
    geom_type = geometry.get("type")
    coordinates = geometry.get("coordinates")

    if not coordinates:
        return False

    if geom_type == "Polygon":
        return is_point_in_polygon(lat, lon, coordinates[0])
    
    elif geom_type == "MultiPolygon":
        return is_point_in_multipolygon(lat, lon, coordinates)

    return False


def find_polygons_containing_point(geojson: dict, lat: float, lon: float) -> List[dict]:
    """
    Find all polygons in a GeoJSON FeatureCollection that contain the given point.
    
    Args:
        geojson: GeoJSON FeatureCollection
        lat: Latitude of the point
        lon: Longitude of the point
    
    Returns:
        List of features that contain the point
    """
    results = []
    features = geojson.get("features", [])
    
    for feature in features:
        geometry = feature.get("geometry")
        if geometry and check_point_in_geometry(lat, lon, geometry):
            results.append(feature)
    
    return results
