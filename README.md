# 🗺️ Polygon Hunter API

**Production-ready REST API for finding polygons containing geographic coordinates.**

## 🎯 What It Does

Given a geographic coordinate (latitude, longitude), the API:
1. Converts coordinates to QuadKey using the tile system
2. Finds the corresponding GeoJSON file from a CSV index (266 tiles)
3. Searches for polygons that contain the point using ray-casting algorithm
4. Returns matching polygons with geometry in GeoJSON format

## ⚡ Quick Start

### Installation
```bash
uv sync
```

### Start API Server
```bash
uv run python -m uvicorn app:app --reload --port 8000
```

Then visit: `http://localhost:8000/docs` for interactive API documentation.

---

## 📡 API Endpoints

### 1. GeoJSON Response (Single Point)
```bash
GET /geojson?lat=40.9887&lon=29.0252
```
Returns polygons as a **GeoJSON FeatureCollection**.

### 2. GeoJSON Response (Batch)
```bash
POST /batch-geojson
Content-Type: application/json

{
  "coordinates": [[40.9887, 29.0252], [41.033, 26.7188]]
}
```
Returns all matching polygons for multiple coordinates as GeoJSON.

### 3. Single Search (JSON)
```bash
GET /search?lat=40.9887&lon=29.0252
```
Returns detailed search result with metadata.

### 4. Batch Search (JSON)
```bash
POST /batch
Content-Type: application/json

{
  "coordinates": [[40.9887, 29.0252], [41.033, 26.7188]]
}
```
Process up to 100 coordinates in one request.

### 5. Health Check
```bash
GET /health
```
System status and statistics.

---

## 🏗️ Architecture

```
FastAPI REST Layer (app.py)
           ↓
Core API Service (api.py)
           ↓
┌──────────────────────────────────────┐
│ • QuadKey Converter (services/quadkey.py) │
│ • Point-in-Polygon (services/geometry.py) │
│ • CSV Index (services/index.py)           │
└──────────────────────────────────────┘
           ↓
GeoJSON Files (data2/ - 266 tiles)
```

## 📁 Project Structure

```
polygon_hunter/
├── app.py                 # FastAPI REST endpoints
├── api.py                 # Core API service
├── models.py              # Data models
├── utils.py               # Utilities & logging
├── services/
│   ├── quadkey.py         # QuadKey conversion
│   ├── geometry.py        # Point-in-polygon detection
│   └── index.py           # QuadKey indexing
├── data2/                 # 266 GeoJSON files
├── test_excel/            # Excel to GeoJSON converter
│   ├── excel_to_geojson.py
│   └── *.xlsx
└── polygon_counts_summary2.csv  # QuadKey index
```

## 🔧 Excel to GeoJSON Converter

Convert Excel files with coordinates to GeoJSON:

```bash
# Start API first
uv run python -m uvicorn app:app --port 8000

# Run converter
uv run python test_excel/excel_to_geojson.py --file "test_excel/data.xlsx"
```

Options:
- `--file`: Excel file path
- `--coord-col`: Combined coordinate column name
- `--lat-col` / `--lon-col`: Separate lat/lon columns
- `--mode`: Output mode (`polygons`, `points`, `both`)
- `--api-url`: API base URL

## 📋 Example Response

```bash
curl "http://localhost:8000/geojson?lat=40.9637&lon=29.0652"
```

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[29.065, 40.963], ...]]
      },
      "properties": {
        "height": -1.0,
        "confidence": 0.967,
        "search_point": {"lat": 40.9637, "lon": 29.0652},
        "quadkey": "122101001"
      }
    }
  ],
  "metadata": {
    "query_point": {"lat": 40.9637, "lon": 29.0652},
    "quadkey": "122101001",
    "total_polygons": 1
  }
}
```

## 📜 License

MIT
