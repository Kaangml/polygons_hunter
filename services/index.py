"""
QuadKey indexing service.

Manages the mapping between QuadKey tiles and GeoJSON files.
Loads and caches the index from CSV for fast lookups.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class QuadKeyIndex:
    """Manages QuadKey to file mapping using CSV index."""

    def __init__(self, csv_path: Path):
        """
        Initialize QuadKey index from CSV file.

        The CSV should have columns: file, total_features, etc.
        The 'file' column contains paths like 'data2/120323223.geojson'

        Args:
            csv_path: Path to the CSV index file

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            Exception: If CSV parsing fails
        """
        self.csv_path = Path(csv_path)
        self.quadkey_to_file: Dict[str, Path] = {}
        self._load_index()

    def _load_index(self) -> None:
        """Load QuadKey to file mapping from CSV."""
        try:
            with open(self.csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    file_path = row["file"].strip()
                    # Extract QuadKey from filename
                    # Example: "data2/120323223.geojson" → "120323223"
                    quadkey = Path(file_path).stem
                    # Store only the filename without directory prefix
                    self.quadkey_to_file[quadkey] = Path(file_path).name

            logger.info(f"Loaded {len(self.quadkey_to_file)} QuadKeys from index")
        except FileNotFoundError:
            logger.error(f"Index file not found: {self.csv_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to load index from {self.csv_path}: {e}")
            raise

    def get_file_for_quadkey(self, quadkey: str) -> Optional[Path]:
        """
        Get the GeoJSON file path for a given QuadKey.

        Args:
            quadkey: QuadKey string

        Returns:
            Path to the GeoJSON file, or None if not found
        """
        return self.quadkey_to_file.get(quadkey)

    def has_quadkey(self, quadkey: str) -> bool:
        """
        Check if QuadKey exists in index.

        Args:
            quadkey: QuadKey string

        Returns:
            True if QuadKey is in index, False otherwise
        """
        return quadkey in self.quadkey_to_file

    def list_all_quadkeys(self) -> List[str]:
        """
        Get list of all available QuadKeys.

        Returns:
            List of QuadKey strings
        """
        return list(self.quadkey_to_file.keys())

    def count(self) -> int:
        """Get total number of indexed QuadKeys."""
        return len(self.quadkey_to_file)
