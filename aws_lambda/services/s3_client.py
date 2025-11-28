"""
AWS S3 Client for Polygon Hunter Lambda.

S3'ten quadkey index ve gzip'li GeoJSON dosyalarını okur.
Memory cache ile warm Lambda instance'larda performans sağlar.
"""

import os
import gzip
import json
import csv
from io import StringIO
from typing import Dict, Optional, Any
from functools import lru_cache

import boto3
from botocore.config import Config


# S3 client configuration for better performance
S3_CONFIG = Config(
    retries={"max_attempts": 3, "mode": "standard"},
    connect_timeout=5,
    read_timeout=10,
)

# Environment variables
BUCKET_NAME = os.environ.get("S3_BUCKET", "polygons-hunter-data")
INDEX_KEY = os.environ.get("INDEX_KEY", "index/quadkey_index.csv")


class S3DataClient:
    """
    S3 client for reading polygon data.
    
    Features:
    - QuadKey index caching (warm Lambda'larda memory'de kalır)
    - Gzip decompression
    - JSON parsing
    """
    
    def __init__(self, bucket_name: str = None):
        """
        Initialize S3 client.
        
        Args:
            bucket_name: S3 bucket name (default: from environment)
        """
        self.bucket = bucket_name or BUCKET_NAME
        self.s3 = boto3.client("s3", config=S3_CONFIG)
        self._index_cache: Optional[Dict[str, Dict]] = None
    
    def get_index(self) -> Dict[str, Dict]:
        """
        Get quadkey index from S3 (cached).
        
        Returns:
            Dict mapping quadkey to metadata:
            {
                "120322312": {
                    "s3_path": "tiles/120322312.geojson.gz",
                    "polygon_count": 938,
                    ...
                },
                ...
            }
        """
        if self._index_cache is not None:
            return self._index_cache
        
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=INDEX_KEY)
            csv_content = response["Body"].read().decode("utf-8")
            
            index = {}
            reader = csv.DictReader(StringIO(csv_content))
            for row in reader:
                quadkey = row["quadkey"]
                index[quadkey] = {
                    "s3_path": row["s3_path"],
                    "polygon_count": int(row.get("polygon_count", 0)),
                    "compressed_size_bytes": int(row.get("compressed_size_bytes", 0)),
                }
            
            self._index_cache = index
            return index
            
        except Exception as e:
            print(f"Error loading index from S3: {e}")
            return {}
    
    def has_quadkey(self, quadkey: str) -> bool:
        """Check if a quadkey exists in the index."""
        return quadkey in self.get_index()
    
    def get_quadkey_info(self, quadkey: str) -> Optional[Dict]:
        """Get metadata for a quadkey."""
        return self.get_index().get(quadkey)
    
    def get_geojson(self, quadkey: str) -> Optional[Dict[str, Any]]:
        """
        Get GeoJSON data for a quadkey from S3.
        
        Args:
            quadkey: QuadKey string
        
        Returns:
            GeoJSON FeatureCollection dict or None if not found
        """
        info = self.get_quadkey_info(quadkey)
        if not info:
            return None
        
        s3_path = info["s3_path"]
        
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=s3_path)
            compressed_data = response["Body"].read()
            
            # Decompress gzip
            json_bytes = gzip.decompress(compressed_data)
            geojson = json.loads(json_bytes.decode("utf-8"))
            
            return geojson
            
        except Exception as e:
            print(f"Error loading GeoJSON for {quadkey}: {e}")
            return None
    
    def get_all_quadkeys(self) -> list:
        """Get list of all available quadkeys."""
        return list(self.get_index().keys())
    
    def get_stats(self) -> Dict:
        """Get statistics about the data."""
        index = self.get_index()
        
        total_polygons = sum(info.get("polygon_count", 0) for info in index.values())
        total_size = sum(info.get("compressed_size_bytes", 0) for info in index.values())
        
        return {
            "total_quadkeys": len(index),
            "total_polygons": total_polygons,
            "total_compressed_size_mb": round(total_size / (1024 * 1024), 2),
            "bucket": self.bucket,
        }


# Singleton instance for Lambda warm reuse
_client_instance: Optional[S3DataClient] = None


def get_s3_client() -> S3DataClient:
    """Get S3 client singleton (for Lambda warm reuse)."""
    global _client_instance
    if _client_instance is None:
        _client_instance = S3DataClient()
    return _client_instance
