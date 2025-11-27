"""
Geometry service - Point-in-polygon detection.

Implements geometric algorithms for determining if a point is inside
a polygon or multipolygon using the ray casting algorithm.
"""

from typing import List

from models import Point


class PointInPolygon:
    """Point-in-polygon detection using ray casting algorithm."""

    @staticmethod
    def is_point_in_polygon(point: Point, polygon_coords: List[List[float]]) -> bool:
        """
        Check if a point is inside a polygon using the ray casting algorithm.

        The ray casting algorithm works by casting a ray from the point to infinity
        and counting how many times it intersects the polygon's edges. If odd,
        the point is inside; if even, it's outside.

        Args:
            point: Point to check
            polygon_coords: List of [lon, lat] coordinates forming the polygon ring

        Returns:
            True if point is inside polygon, False otherwise

        Reference:
            https://en.wikipedia.org/wiki/Point_in_polygon
        """
        if len(polygon_coords) < 3:
            return False

        x, y = point.lon, point.lat
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

    @staticmethod
    def is_point_in_multipolygon(
        point: Point, multipolygon_coords: List[List[List[float]]]
    ) -> bool:
        """
        Check if a point is inside any polygon in a multipolygon.

        Args:
            point: Point to check
            multipolygon_coords: List of polygons, each polygon is a list of rings

        Returns:
            True if point is inside any polygon, False otherwise
        """
        for polygon in multipolygon_coords:
            if polygon and PointInPolygon.is_point_in_polygon(point, polygon[0]):
                return True
        return False

    @staticmethod
    def check_point_in_geometry(point: Point, geometry: dict) -> bool:
        """
        Check if point is in a GeoJSON geometry object.

        Handles multiple geometry types: Polygon, MultiPolygon, etc.

        Args:
            point: Point to check
            geometry: GeoJSON geometry object

        Returns:
            True if point is inside geometry
        """
        geom_type = geometry.get("type")
        coordinates = geometry.get("coordinates")

        if not coordinates:
            return False

        if geom_type == "Polygon":
            # For Polygon: coordinates[0] is exterior ring
            return PointInPolygon.is_point_in_polygon(point, coordinates[0])

        elif geom_type == "MultiPolygon":
            # For MultiPolygon: each item is a Polygon
            return PointInPolygon.is_point_in_multipolygon(point, coordinates)

        return False
