"""
Test script for Polygon Hunter REST API.

Tests all endpoints without actually starting the server.
"""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    print("\n" + "=" * 80)
    print("TEST: Root Endpoint")
    print("=" * 80)

    response = client.get("/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200


def test_health():
    """Test health check endpoint."""
    print("\n" + "=" * 80)
    print("TEST: Health Check")
    print("=" * 80)

    response = client.get("/health")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Status: {data['status']}")
    print(f"Indexed QuadKeys: {data['quadkeys_indexed']}")
    assert response.status_code == 200
    assert data["status"] == "healthy"


def test_search_single():
    """Test single coordinate search."""
    print("\n" + "=" * 80)
    print("TEST: Single Coordinate Search")
    print("=" * 80)

    response = client.get("/search?lat=40.9887&lon=29.0252")
    print(f"Status: {response.status_code}")
    data = response.json()

    print(f"Query Status: {data['status']}")
    print(f"QuadKey: {data['quadkey']}")
    print(f"File: {data['file']}")
    print(f"Polygons Found: {data['count']}")

    assert response.status_code == 200
    assert data["status"] == "success"
    return data


def test_search_invalid():
    """Test invalid coordinate input."""
    print("\n" + "=" * 80)
    print("TEST: Invalid Coordinate (should fail)")
    print("=" * 80)

    response = client.get("/search?lat=95.0&lon=29.0")
    print(f"Status: {response.status_code}")
    assert response.status_code == 422  # Validation error


def test_batch_search():
    """Test batch coordinate search."""
    print("\n" + "=" * 80)
    print("TEST: Batch Coordinate Search")
    print("=" * 80)

    payload = {
        "coordinates": [
            [40.9887, 29.0252],
            [41.0330, 26.7188],
            [42.0, 27.0],
        ]
    }

    response = client.post("/batch", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()

    print(f"Results: {len(data)} coordinates processed")
    for i, result in enumerate(data):
        print(f"  [{i}] QuadKey: {result['quadkey']}, "
              f"Polygons: {result['count']}, Status: {result['status']}")

    assert response.status_code == 200
    assert len(data) == 3


def test_quadkey_info():
    """Test QuadKey information endpoint."""
    print("\n" + "=" * 80)
    print("TEST: QuadKey Information")
    print("=" * 80)

    response = client.get("/quadkey-info/120323223")
    print(f"Status: {response.status_code}")
    data = response.json()

    print(f"QuadKey: {data['quadkey']}")
    print(f"Zoom: {data['zoom']}")
    bbox = data["bounding_box"]
    print(f"BBox - Lat: {bbox['min_lat']:.4f} to {bbox['max_lat']:.4f}")
    print(f"BBox - Lon: {bbox['min_lon']:.4f} to {bbox['max_lon']:.4f}")
    print(f"File: {data['file']}")
    print(f"File Exists: {data['file_exists']}")

    assert response.status_code == 200
    assert data["quadkey"] == "120323223"


def test_available_quadkeys():
    """Test list available QuadKeys."""
    print("\n" + "=" * 80)
    print("TEST: Available QuadKeys")
    print("=" * 80)

    response = client.get("/available-quadkeys?limit=10")
    print(f"Status: {response.status_code}")
    data = response.json()

    print(f"Total QuadKeys: {data['total']}")
    print(f"Returned: {len(data['quadkeys'])}")
    print(f"Sample: {data['quadkeys'][:5]}")

    assert response.status_code == 200
    assert data["total"] > 0


def run_all_tests():
    """Run all tests."""
    print("\n" + "🚀" * 40)
    print("POLYGON HUNTER REST API - TEST SUITE")
    print("🚀" * 40)

    tests = [
        ("Root Endpoint", test_root),
        ("Health Check", test_health),
        ("Single Search", test_search_single),
        ("Invalid Input", test_search_invalid),
        ("Batch Search", test_batch_search),
        ("QuadKey Info", test_quadkey_info),
        ("Available QuadKeys", test_available_quadkeys),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            test_func()
            results[test_name] = "✓ PASS"
        except AssertionError as e:
            print(f"\n✗ Assertion failed: {e}")
            results[test_name] = "✗ FAIL"
        except Exception as e:
            print(f"\n✗ Error: {e}")
            results[test_name] = "! ERROR"

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for test_name, result in results.items():
        print(f"{result} - {test_name}")

    all_passed = all(r.startswith("✓") for r in results.values())
    print("\n" + ("=" * 80))
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("=" * 80 + "\n")

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
