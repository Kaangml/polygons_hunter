# 🚀 AWS Lambda + S3 Deployment Plan

## 📋 Genel Bakış

Polygon Hunter API'yi AWS Lambda + S3 üzerinde serverless olarak çalıştırmak için gerekli adımlar.

---

## 🏗️ Mimari

```
┌──────────────────────────────────────────────────────────────────────┐
│                          API Gateway                                  │
│                    GET /search?lat=X&lon=Y                           │
│                    POST /batch                                        │
│                    GET /geojson?lat=X&lon=Y                          │
└──────────────────────────┬───────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────────┐
│                         AWS Lambda                                    │
│                      (Python 3.11 + FastAPI + Mangum)                │
│                                                                       │
│  İş Akışı:                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ 1. Gelen koordinatı al (lat, lon)                               │ │
│  │ 2. QuadKey hesapla (zoom=9)                                     │ │
│  │ 3. S3'ten quadkey_index.csv kontrol et (memory cache)          │ │
│  │ 4. QuadKey varsa → ilgili .geojson.gz dosyasını S3'ten al      │ │
│  │ 5. Gzip decompress + JSON parse                                 │ │
│  │ 6. Point-in-Polygon kontrolü (ray-casting)                     │ │
│  │ 7. Sonucu GeoJSON olarak döndür                                │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────────┐
│                          S3 Bucket                                    │
│                    (polygons-hunter-data)                            │
│                                                                       │
│  Yapı:                                                               │
│  ├── index/                                                          │
│  │   └── quadkey_index.csv        # QuadKey → dosya yolu eşlemesi   │
│  │                                                                    │
│  └── tiles/                                                          │
│      ├── 120322312.geojson.gz     # Gzip'li GeoJSON dosyaları       │
│      ├── 120322321.geojson.gz                                        │
│      ├── 120322323.geojson.gz                                        │
│      └── ... (toplam 266 dosya)                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Dosya Yapısı

```
polygon_hunter/
├── aws_lambda/                      # AWS Lambda kodu
│   ├── handler.py                   # Lambda entry point (Mangum)
│   ├── app.py                       # FastAPI app
│   ├── services/
│   │   ├── __init__.py
│   │   ├── s3_client.py            # S3 işlemleri
│   │   ├── quadkey.py              # QuadKey hesaplama
│   │   └── geometry.py             # Point-in-polygon
│   ├── models.py                    # Pydantic modeller
│   ├── requirements.txt             # Lambda dependencies
│   └── template.yaml               # SAM template (opsiyonel)
│
├── scripts/
│   ├── prepare_s3_data.py          # GeoJSON'ları gzip'le ve index oluştur
│   ├── upload_to_s3.py             # S3'e yükle
│   └── deploy_lambda.py            # Lambda deployment
│
└── data2/                           # Mevcut GeoJSON dosyaları
```

---

## 📦 Adım Adım Uygulama

### ADIM 1: S3 Veri Hazırlığı
**Dosya:** `scripts/prepare_s3_data.py`

```python
# Bu script:
# 1. data2/ içindeki tüm GeoJSON dosyalarını okur
# 2. Her birini gzip'ler
# 3. quadkey_index.csv oluşturur:
#    quadkey,s3_path,polygon_count,file_size_bytes
#    120322312,tiles/120322312.geojson.gz,45,12340
#    120322321,tiles/120322321.geojson.gz,23,8920
#    ...
```

**Çıktı:**
- `s3_data/tiles/*.geojson.gz` - Gzip'li dosyalar
- `s3_data/index/quadkey_index.csv` - Index dosyası

---

### ADIM 2: S3 Bucket Oluştur ve Yükle
**Dosya:** `scripts/upload_to_s3.py`

```bash
# AWS CLI ile bucket oluştur
aws s3 mb s3://polygons-hunter-data --region eu-central-1

# Dosyaları yükle
aws s3 sync s3_data/ s3://polygons-hunter-data/
```

**S3 Yapısı:**
```
s3://polygons-hunter-data/
├── index/quadkey_index.csv
└── tiles/
    ├── 120322312.geojson.gz
    ├── 120322321.geojson.gz
    └── ...
```

---

### ADIM 3: Lambda Fonksiyonu Geliştir
**Dosya:** `aws_lambda/app.py`

```python
from fastapi import FastAPI, Query
from mangum import Mangum
import boto3
import gzip
import json
from functools import lru_cache

app = FastAPI(title="Polygon Hunter API - AWS Lambda")
s3 = boto3.client('s3')
BUCKET = "polygons-hunter-data"

# Index'i cache'le (Lambda warm instance'da kalır)
@lru_cache(maxsize=1)
def get_index():
    response = s3.get_object(Bucket=BUCKET, Key="index/quadkey_index.csv")
    # CSV parse et ve dict döndür
    ...

@app.get("/search")
def search(lat: float, lon: float):
    # 1. QuadKey hesapla
    quadkey = lat_lon_to_quadkey(lat, lon, zoom=9)
    
    # 2. Index'te kontrol et
    index = get_index()
    if quadkey not in index:
        return {"found": False, "message": "QuadKey not in coverage"}
    
    # 3. S3'ten gzip dosyasını al
    s3_path = index[quadkey]["s3_path"]
    response = s3.get_object(Bucket=BUCKET, Key=s3_path)
    
    # 4. Decompress ve parse
    geojson = json.loads(gzip.decompress(response['Body'].read()))
    
    # 5. Point-in-polygon kontrolü
    results = find_polygons_containing_point(geojson, lat, lon)
    
    return {"found": bool(results), "polygons": results}

# Lambda handler
handler = Mangum(app)
```

---

### ADIM 4: Lambda Deployment
**Seçenek A: AWS SAM (Önerilen)**

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  PolygonHunterFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.handler
      Runtime: python3.11
      MemorySize: 512
      Timeout: 30
      Environment:
        Variables:
          S3_BUCKET: polygons-hunter-data
      Policies:
        - S3ReadPolicy:
            BucketName: polygons-hunter-data
      Events:
        Api:
          Type: Api
          Properties:
            Path: /{proxy+}
            Method: ANY
```

**Seçenek B: Docker Container (Daha büyük paketler için)**

```dockerfile
FROM public.ecr.aws/lambda/python:3.11
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY aws_lambda/ ${LAMBDA_TASK_ROOT}/
CMD ["handler.handler"]
```

---

## ⏱️ Zaman Çizelgesi

| Adım | Açıklama | Süre |
|------|----------|------|
| 1 | S3 veri hazırlığı scripti | 30 dk |
| 2 | S3 upload scripti | 15 dk |
| 3 | Lambda FastAPI app | 1 saat |
| 4 | S3 client + caching | 30 dk |
| 5 | Test ve debug | 1 saat |
| 6 | SAM/CloudFormation template | 30 dk |
| 7 | Deployment ve test | 30 dk |
| **Toplam** | | **~4-5 saat** |

---

## 📊 Beklenen Performans

| Metrik | Değer |
|--------|-------|
| Cold Start | ~800ms - 1.5s |
| Warm Request | ~100-200ms |
| S3 Index Okuma (cached) | 0ms |
| S3 GeoJSON Okuma | ~50-100ms |
| Gzip Decompress | ~10-20ms |
| Point-in-Polygon | ~5-10ms |
| **Toplam Warm** | **~150-300ms** |

---

## 💰 Maliyet Tahmini

| Kaynak | Birim Fiyat | Aylık (100K istek) |
|--------|-------------|---------------------|
| Lambda | $0.20/1M istek | ~$0.02 |
| Lambda Compute | $0.0000166/GB-s | ~$0.50 |
| S3 Storage | $0.023/GB | ~$0.01 |
| S3 GET | $0.0004/1K istek | ~$0.04 |
| API Gateway | $3.50/1M istek | ~$0.35 |
| **Toplam** | | **~$1/ay** |

---

## ✅ Checklist

- [x] **ADIM 1:** `scripts/prepare_s3_data.py` oluştur ✅
- [x] **ADIM 2:** Gzip dosyaları ve index'i oluştur (local test) ✅
  - 266 dosya işlendi
  - ~20.8 milyon polygon
  - 8.6 GB → 1.7 GB (%80 küçülme)
- [ ] **ADIM 3:** S3 bucket oluştur (AWS Console veya CLI)
- [ ] **ADIM 4:** S3'e dosyaları yükle
- [x] **ADIM 5:** `aws_lambda/` dizini oluştur ✅
- [x] **ADIM 6:** FastAPI + Mangum app yaz ✅
- [x] **ADIM 7:** S3 client ve caching implement et ✅
- [ ] **ADIM 8:** Local test (SAM local)
- [ ] **ADIM 9:** Lambda deploy et
- [ ] **ADIM 10:** API Gateway yapılandır
- [ ] **ADIM 11:** End-to-end test
- [ ] **ADIM 12:** README güncelle

---

## 🔧 Gerekli AWS Kaynakları

1. **S3 Bucket:** `polygons-hunter-data`
2. **Lambda Function:** `polygon-hunter-api`
3. **API Gateway:** REST API
4. **IAM Role:** Lambda için S3 read erişimi

---

## 🚀 Başlayalım!

İlk adım olarak S3 veri hazırlığı scriptini yazalım.
