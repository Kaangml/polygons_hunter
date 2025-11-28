"""
AWS Lambda için QuadKey conversion service.

Mevcut services/quadkey.py'nin Lambda için optimize edilmiş versiyonu.
"""

import math
from typing import Tuple, NamedTuple


class BoundingBox(NamedTuple):
    """Geographic bounding box."""
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float


def latlon_to_quadkey(lat: float, lon: float, zoom: int = 9) -> str:
    """
    Convert latitude/longitude to QuadKey at a given zoom level.
    
    Args:
        lat: Latitude coordinate (-90 to 90)
        lon: Longitude coordinate (-180 to 180)
        zoom: Zoom level (default: 9)
    
    Returns:
        QuadKey string (e.g., "120323223")
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


def quadkey_to_bbox(quadkey: str) -> BoundingBox:
    """
    Convert QuadKey to its bounding box (geographic extent).
    
    Args:
        quadkey: QuadKey string
    
    Returns:
        BoundingBox with min/max latitude and longitude
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
