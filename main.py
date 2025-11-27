"""
Test suite and entry point for Polygon Hunter API.

Demonstrates:
- Single coordinate search
- Batch processing
- QuadKey information retrieval
- Error handling
- Edge cases
"""

import logging
from pathlib import Path

from models import Point
from api import PolygonHunterAPI
from utils import configure_logging, get_logger

logger = get_logger(__name__)


class PolygonHunterDemo:
    """Demo and test suite for the Polygon Hunter API."""

    def __init__(self, data_dir: Path, csv_path: Path):
        """Initialize demo with API instance."""
        self.api = PolygonHunterAPI(data_dir, csv_path, zoom_level=9)

    def test_single_search(self):
        """Test 1: Search for polygons at a single coordinate."""
        print("\n" + "=" * 80)
        print("TEST 1: Single Coordinate Search")
        print("=" * 80)

        point = Point(lat=40.98871847420657, lon=29.025198061764637)
        result = self.api.find_polygons(point)

        print(f"Input: ({point.lat}, {point.lon})")
        print(f"Status: {result.status}")
        print(f"QuadKey: {result.quadkey}")
        print(f"File: {result.file}")
        print(f"Polygons Found: {result.count}")

        if result.polygons:
            print(f"\nFirst polygon properties (sample):")
            props = result.polygons[0]["properties"]
            for i, (key, value) in enumerate(props.items()):
                if i >= 3:
                    break
                print(f"  {key}: {value}")

        return result.status == "success"

    def test_quadkey_info(self, quadkey: str):
        """Test 2: Get information about a QuadKey tile."""
        print("\n" + "=" * 80)
        print("TEST 2: QuadKey Information")
        print("=" * 80)

        info = self.api.get_quadkey_info(quadkey)

        print(f"QuadKey: {info.quadkey}")
        print(f"Zoom Level: {info.zoom}")
        bbox = info.bounding_box
        print(f"Bounding Box:")
        print(f"  Latitude:  {bbox.min_lat:.6f} to {bbox.max_lat:.6f}")
        print(f"  Longitude: {bbox.min_lon:.6f} to {bbox.max_lon:.6f}")
        print(f"File: {info.file}")
        print(f"File Exists: {info.file_exists}")

        return info.file_exists

    def test_batch_search(self):
        """Test 3: Search multiple coordinates in batch."""
        print("\n" + "=" * 80)
        print("TEST 3: Batch Processing")
        print("=" * 80)

        test_points = [
            (40.98871847420657, 29.025198061764637),
            (41.0329743324414, 26.71875),
            (42.0, 27.0),
        ]

        results = self.api.find_polygons_batch(test_points)

        for i, result in enumerate(results):
            print(f"\nPoint {i + 1}: ({test_points[i][0]}, {test_points[i][1]})")
            print(f"  Status: {result.status}")
            print(f"  QuadKey: {result.quadkey}")
            print(f"  Polygons: {result.count}")

        success_count = sum(1 for r in results if r.status == "success")
        print(f"\nSuccessful searches: {success_count}/{len(results)}")

        return success_count > 0

    def test_edge_cases(self):
        """Test 4: Edge cases and boundary conditions."""
        print("\n" + "=" * 80)
        print("TEST 4: Edge Cases")
        print("=" * 80)

        edge_cases = [
            (0.0, 0.0, "Equator/Prime Meridian"),
            (40.0, 20.0, "Turkey region"),
            (-45.0, 45.0, "Southern Hemisphere"),
        ]

        results = []
        for lat, lon, description in edge_cases:
            try:
                point = Point(lat, lon)
                result = self.api.find_polygons(point)
                status = "✓" if result.status == "success" else "✗"
                print(
                    f"{status} ({lat:6.1f}, {lon:6.1f}) - {description:25} "
                    f"→ QuadKey: {result.quadkey}, Polygons: {result.count}"
                )
                results.append(result.status == "success" or result.status == "error")
            except Exception as e:
                print(
                    f"✗ ({lat:6.1f}, {lon:6.1f}) - {description:25} "
                    f"→ Error: {str(e)[:40]}"
                )
                results.append(False)

        return all(results)

    def test_invalid_input(self):
        """Test 5: Invalid input handling."""
        print("\n" + "=" * 80)
        print("TEST 5: Invalid Input Handling")
        print("=" * 80)

        invalid_inputs = [
            (95.0, 29.0, "Invalid latitude (> 90)"),
            (-95.0, 29.0, "Invalid latitude (< -90)"),
            (40.0, 185.0, "Invalid longitude (> 180)"),
            (40.0, -185.0, "Invalid longitude (< -180)"),
        ]

        for lat, lon, description in invalid_inputs:
            try:
                point = Point(lat, lon)
                print(f"✗ {description:40} - Should have raised error!")
            except ValueError as e:
                print(f"✓ {description:40} - {str(e)[:50]}")

        return True

    def run_all_tests(self):
        """Run all tests."""
        print("\n" + "🚀" * 40)
        print("POLYGON HUNTER API - COMPREHENSIVE TEST SUITE")
        print("🚀" * 40)

        tests = [
            ("Single Search", self.test_single_search, ()),
            ("Batch Search", self.test_batch_search, ()),
            ("Edge Cases", self.test_edge_cases, ()),
            ("Invalid Input", self.test_invalid_input, ()),
        ]

        results = {}
        for test_name, test_func, args in tests:
            try:
                passed = test_func(*args)
                results[test_name] = "PASS" if passed else "FAIL"
            except Exception as e:
                logger.error(f"Test {test_name} failed: {e}", exc_info=True)
                results[test_name] = "ERROR"

        # Get QuadKey info for the first test
        try:
            results["QuadKey Info"] = "PASS" if self.test_quadkey_info(
                "120323223"
            ) else "FAIL"
        except Exception as e:
            logger.error(f"QuadKey info test failed: {e}")
            results["QuadKey Info"] = "ERROR"

        # Print summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        for test_name, result in results.items():
            status_icon = "✓" if result == "PASS" else "✗" if result == "FAIL" else "!"
            print(f"{status_icon} {test_name:30} {result}")

        all_passed = all(r == "PASS" for r in results.values())
        print("\n" + ("=" * 80))
        if all_passed:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("⚠️  SOME TESTS FAILED")
        print("=" * 80 + "\n")

        return all_passed


def main():
    """Entry point."""
    configure_logging(logging.INFO)

    # Configuration
    DATA_DIR = Path(
        "/Users/kaan/Desktop/Kaan/MapinData/polgyon_hunter/data2"
    )
    CSV_PATH = Path(
        "/Users/kaan/Desktop/Kaan/MapinData/polgyon_hunter/polygon_counts_summary2.csv"
    )

    try:
        demo = PolygonHunterDemo(DATA_DIR, CSV_PATH)
        all_passed = demo.run_all_tests()
        return 0 if all_passed else 1
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
