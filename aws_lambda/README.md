# Polygon Hunter - AWS Lambda

Bu klasör AWS Lambda üzerinde çalışacak serverless API kodlarını içerir.

## 📁 Yapı

```
aws_lambda/
├── handler.py          # Lambda entry point (Mangum)
├── app.py             # FastAPI uygulaması
├── models.py          # Pydantic modeller
├── requirements.txt   # Python dependencies
├── template.yaml      # AWS SAM template
└── services/
    ├── __init__.py
    ├── quadkey.py     # QuadKey hesaplama
    ├── geometry.py    # Point-in-polygon
    └── s3_client.py   # S3 işlemleri
```

## 🚀 Deployment

### Ön Gereksinimler

1. **AWS CLI** yapılandırılmış olmalı:
   ```bash
   aws configure
   ```

2. **AWS SAM CLI** yüklü olmalı:
   ```bash
   brew install aws-sam-cli  # macOS
   ```

3. **S3 verileri yüklenmiş olmalı** (scripts/upload_to_s3.py ile)

### Build & Deploy

```bash
# aws_lambda dizinine git
cd aws_lambda

# SAM ile build et
sam build

# Deploy et (guided mode - ilk kez)
sam deploy --guided

# Sonraki deploymentlar
sam deploy
```

### Alternatif: Docker ile Deploy

```bash
# Docker image build
sam build --use-container

# Deploy
sam deploy --guided
```

## 🧪 Local Test

### SAM Local API

```bash
# Local API Gateway başlat
sam local start-api

# Test et
curl "http://localhost:3000/search?lat=40.9637&lon=29.0652"
```

### Direkt Python

```bash
cd aws_lambda
pip install -r requirements.txt
python handler.py  # uvicorn ile başlar

curl "http://localhost:8000/search?lat=40.9637&lon=29.0652"
```

## 📡 API Endpoints

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/health` | Health check + S3 status |
| GET | `/search?lat=X&lon=Y` | Tekil koordinat arama |
| POST | `/batch` | Çoklu koordinat arama |
| GET | `/geojson?lat=X&lon=Y` | GeoJSON olarak döndür |
| POST | `/batch-geojson` | Çoklu koordinat GeoJSON |
| GET | `/quadkeys` | Mevcut quadkey listesi |
| GET | `/stats` | İstatistikler |

## ⚙️ Konfigürasyon

Environment variables:

| Variable | Default | Açıklama |
|----------|---------|----------|
| `S3_BUCKET` | `polygons-hunter-data` | S3 bucket adı |
| `INDEX_KEY` | `index/quadkey_index.csv` | Index dosyası yolu |

## 📊 Performans

| Metrik | Değer |
|--------|-------|
| Cold Start | ~800ms - 1.5s |
| Warm Request | ~100-200ms |
| Memory | 512 MB |
| Timeout | 30 saniye |
