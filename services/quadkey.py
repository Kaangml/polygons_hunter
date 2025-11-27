"""
QuadKey conversion service.

Handles conversion between geographic coordinates (latitude/longitude)
and QuadKey tile system used for spatial indexing.
"""

import math
from typing import Tuple

from models import BoundingBox


class QuadKeyConverter:
    """Converts between coordinates and QuadKey tile system."""

    @staticmethod
    def latlon_to_quadkey(lat: float, lon: float, zoom: int) -> str:
        """
        Convert latitude/longitude to QuadKey at a given zoom level.

        The QuadKey system is used by Microsoft Bing Maps for spatial indexing.
        Each QuadKey represents a rectangular tile at a specific zoom level.

        Args:
            lat: Latitude coordinate (-90 to 90)
            lon: Longitude coordinate (-180 to 180)
            zoom: Zoom level (determines tile granularity, typically 1-28)

        Returns:
            QuadKey string (e.g., "120323223")

        Example:
            >>> qk = QuadKeyConverter.latlon_to_quadkey(40.98871847420657, 29.025198061764637, 9)
            >>> qk
            '120323223'
        """
        # Normalize latitude to avoid edge cases
        sin_lat = math.sin(lat * math.pi / 180.0)
        sin_lat = min(max(sin_lat, -0.9999), 0.9999)

        n = 2 ** zoom
        # Calculate tile X coordinate (longitude-based)
        tileX = int((lon + 180.0) / 360.0 * n)
        # Calculate tile Y coordinate (latitude-based)
        tileY = int(
            (1.0 - math.log((1 + sin_lat) / (1 - sin_lat)) / (2 * math.pi)) * n / 2.0
        )

        # Convert (tileX, tileY) to QuadKey string
        quadkey = ""
        for i in range(zoom, 0, -1):
            digit = 0
            mask = 1 << (i - 1)
            if (tileX & mask) != 0:
                digit += 1
            if (tileY & mask) != 0:
                digit += 2
            quadkey += str(digit)

        return quadkey

    @staticmethod
    def quadkey_to_bbox(quadkey: str) -> BoundingBox:
        """
        Convert QuadKey to its bounding box (geographic extent).

        Args:
            quadkey: QuadKey string

        Returns:
            BoundingBox object with min/max latitude and longitude

        Example:
            >>> bbox = QuadKeyConverter.quadkey_to_bbox('120322312')
            >>> bbox.min_lat
            42.0329743324414
        """
        zoom = len(quadkey)
        tileX = 0
        tileY = 0

        # Decode QuadKey to tile coordinates
        for c in quadkey:
            tileX <<= 1
            tileY <<= 1
            if c == "1":
                tileX |= 1
            elif c == "2":
                tileY |= 1
            elif c == "3":
                tileX |= 1
                tileY |= 1

        n = 2 ** zoom

        # Calculate bounding box corners
        lon_left = tileX / n * 360.0 - 180.0
        lat_top_rad = math.atan(math.sinh(math.pi * (1 - 2 * tileY / n)))
        lat_top = lat_top_rad * 180.0 / math.pi

        lon_right = (tileX + 1) / n * 360.0 - 180.0
        lat_bottom_rad = math.atan(math.sinh(math.pi * (1 - 2 * (tileY + 1) / n)))
        lat_bottom = lat_bottom_rad * 180.0 / math.pi

        return BoundingBox(lat_bottom, lon_left, lat_top, lon_right)

    @staticmethod
    def get_zoom_from_quadkey(quadkey: str) -> int:
        """
        Extract zoom level from QuadKey.

        Args:
            quadkey: QuadKey string

        Returns:
            Zoom level (length of quadkey)
        """
        return len(quadkey)
