# 🧰 AWS Toolkit - Kapsamlı Dokümantasyon

Bu modül AWS servislerini (S3, Lambda, API Gateway) Python ile kullanmak için hazır fonksiyonlar içerir.

---

## 📋 İçindekiler

1. [Hızlı Başlangıç](#-hızlı-başlangıç)
2. [Kurulum](#-kurulum)
3. [Konfigürasyon (AWSConfig)](#-awsconfig---konfigürasyon)
4. [S3 İşlemleri (S3Operations)](#-s3operations---s3-işlemleri)
5. [Lambda İşlemleri (LambdaOperations)](#-lambdaoperations---lambda-işlemleri)
6. [API Gateway İşlemleri](#-apigatewayoperations---api-gateway)
7. [Yardımcı Fonksiyonlar](#-yardımcı-fonksiyonlar-quick-functions)
8. [SAM CLI Kullanımı](#-sam-cli---serverless-application-model)
9. [Gerçek Dünya Örnekleri](#-gerçek-dünya-örnekleri)

---

## 🚀 Hızlı Başlangıç

```python
from aws_toolkit import AWSConfig, S3Operations, LambdaOperations

# Konfigürasyon yükle
config = AWSConfig().load_from_env()

# S3'e dosya yükle
s3 = S3Operations(config, bucket="my-bucket")
s3.upload_file("data.json", "files/data.json")

# Lambda çağır
lam = LambdaOperations(config)
result = lam.invoke("my-function", {"name": "Kaan"})
```

---

## 📦 Kurulum

```bash
# Gerekli paketler
pip install boto3 python-dotenv

# Veya uv ile
uv add boto3 python-dotenv
```

**.env dosyası oluştur:**
```env
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AWS_REGION=eu-central-1
S3_BUCKET=my-bucket-name
```

---

## ⚙️ AWSConfig - Konfigürasyon

AWS credentials yönetimi ve client oluşturma.

### Metodlar

| Metod | Açıklama | Return |
|-------|----------|--------|
| `load_from_env(path)` | .env'den credentials yükle | self |
| `validate()` | Credentials kontrolü | bool |
| `get_client(service)` | Boto3 client oluştur | client |
| `get_resource(service)` | Boto3 resource oluştur | resource |
| `test_connection()` | AWS bağlantısını test et | dict |

### Kullanım Örnekleri

```python
from aws_toolkit import AWSConfig

# 1. .env'den yükle
config = AWSConfig().load_from_env()

# 2. Doğrudan değerlerle
config = AWSConfig(
    access_key="AKIA...",
    secret_key="...",
    region="eu-central-1",
    bucket="my-bucket"
)

# 3. Bağlantı testi
result = config.test_connection()
if result["success"]:
    print(f"Account ID: {result['account_id']}")

# 4. Farklı servisler için client
s3_client = config.get_client('s3')
lambda_client = config.get_client('lambda')
iam_client = config.get_client('iam')
```

---

## 📁 S3Operations - S3 İşlemleri

S3 bucket ve object yönetimi.

### Bucket Metodları

| Metod | Açıklama | Parametreler | Return |
|-------|----------|--------------|--------|
| `list_buckets()` | Tüm bucket'ları listele | - | List[dict] |
| `bucket_exists(bucket)` | Bucket var mı kontrol | bucket: str | bool |
| `create_bucket(bucket, region)` | Yeni bucket oluştur | bucket: str, region: str | dict |
| `delete_bucket(bucket, force)` | Bucket sil | bucket: str, force: bool | dict |

### Object Metodları

| Metod | Açıklama | Parametreler | Return |
|-------|----------|--------------|--------|
| `list_objects(prefix, max_keys)` | Objeleri listele | prefix: str | List[dict] |
| `upload_file(local, s3_key)` | Dosya yükle | local_path, s3_key | dict |
| `upload_bytes(data, s3_key)` | Bytes yükle | data: bytes, s3_key | dict |
| `download_file(s3_key, local)` | Dosya indir | s3_key, local_path | dict |
| `get_object(s3_key, decompress)` | İçerik oku | s3_key, decompress_gzip | dict |
| `delete_object(s3_key)` | Obje sil | s3_key: str | dict |
| `delete_objects(keys)` | Toplu sil | s3_keys: List[str] | dict |
| `object_exists(s3_key)` | Obje var mı | s3_key: str | bool |
| `generate_presigned_url(s3_key)` | Geçici URL | s3_key, expiration | str |

### Kullanım Örnekleri

```python
from aws_toolkit import AWSConfig, S3Operations

config = AWSConfig().load_from_env()
s3 = S3Operations(config, bucket="my-bucket")

# BUCKET İŞLEMLERİ
# ----------------

# Tüm bucket'ları listele
buckets = s3.list_buckets()
for b in buckets:
    print(f"{b['name']} - {b['creation_date']}")

# Bucket oluştur
result = s3.create_bucket("new-bucket-name")
if result["success"]:
    print(f"Oluşturuldu: {result['location']}")

# Bucket sil (içindekilerle birlikte)
s3.delete_bucket("old-bucket", force=True)


# DOSYA YÜKLEME
# -------------

# Basit dosya yükleme
s3.upload_file("local_file.json", "remote/file.json")

# Gzip ile yükleme
s3.upload_file(
    "large_data.json.gz",
    "data/large.json.gz",
    content_type="application/json",
    content_encoding="gzip"
)

# Bytes olarak yükleme (memory'den)
import json
data = {"hello": "world"}
s3.upload_bytes(
    json.dumps(data).encode(),
    "data/inline.json",
    content_type="application/json"
)

# Gzip sıkıştırarak yükleme
import gzip
compressed = gzip.compress(json.dumps(data).encode())
s3.upload_bytes(compressed, "data/compressed.json.gz")


# DOSYA İNDİRME / OKUMA
# ---------------------

# Dosya indir
s3.download_file("remote/file.json", "local_copy.json")

# İçeriği direkt oku
result = s3.get_object("data/file.json")
content = json.loads(result["content"])

# Gzip'li dosyayı oku
result = s3.get_object("data/file.json.gz", decompress_gzip=True)
content = json.loads(result["content"])


# LİSTELEME
# ---------

# Tüm objeler
objects = s3.list_objects()

# Prefix ile filtreleme
objects = s3.list_objects(prefix="data/2024/")

for obj in objects:
    print(f"{obj['key']} - {obj['size']} bytes")


# SİLME
# -----

# Tek obje sil
s3.delete_object("old_file.json")

# Toplu silme
s3.delete_objects(["file1.json", "file2.json", "file3.json"])


# GEÇİCİ URL
# ----------

# 1 saatlik download linki
url = s3.generate_presigned_url("private/document.pdf", expiration=3600)

# 5 dakikalık upload linki
url = s3.generate_presigned_url(
    "uploads/new_file.pdf",
    expiration=300,
    http_method="PUT"
)
```

---

## ⚡ LambdaOperations - Lambda İşlemleri

Lambda fonksiyon yönetimi ve çağırma.

### Metodlar

| Metod | Açıklama | Parametreler | Return |
|-------|----------|--------------|--------|
| `list_functions()` | Fonksiyonları listele | - | List[dict] |
| `get_function(name)` | Fonksiyon detayları | function_name | dict |
| `invoke(name, payload)` | Fonksiyon çağır | function_name, payload, invocation_type | dict |
| `update_function_code(name, zip)` | Kod güncelle | function_name, zip_file veya s3_bucket+s3_key | dict |
| `update_environment(name, vars)` | Env vars güncelle | function_name, variables | dict |

### Kullanım Örnekleri

```python
from aws_toolkit import AWSConfig, LambdaOperations

config = AWSConfig().load_from_env()
lam = LambdaOperations(config)

# FONKSİYONLARI LİSTELE
# ---------------------
functions = lam.list_functions()
for f in functions:
    print(f"{f['name']} ({f['runtime']}) - {f['memory']}MB, {f['timeout']}s")


# FONKSİYON DETAYLARI
# -------------------
info = lam.get_function("my-function")
print(f"Handler: {info['handler']}")
print(f"Environment: {info['environment']}")


# FONKSİYON ÇAĞIRMA
# -----------------

# Senkron çağrı (yanıt bekle)
result = lam.invoke("my-function", {"name": "Kaan", "action": "greet"})
if result["success"]:
    print(f"Response: {result['response']}")

# Asenkron çağrı (fire & forget)
lam.invoke(
    "background-processor",
    {"job_id": "123"},
    invocation_type="Event"
)


# KOD GÜNCELLEME
# --------------

# Lokal zip'ten
lam.update_function_code("my-function", zip_file="deployment.zip")

# S3'ten
lam.update_function_code(
    "my-function",
    s3_bucket="deployments",
    s3_key="functions/my-function-v2.zip"
)


# ENVIRONMENT VARIABLES GÜNCELLEME
# --------------------------------
lam.update_environment("my-function", {
    "S3_BUCKET": "new-bucket",
    "LOG_LEVEL": "DEBUG",
    "API_KEY": "secret-key"
})
```

---

## 🌐 APIGatewayOperations - API Gateway

API Gateway bilgilerini okuma.

> **Not:** SAM ile deploy edilen API'ler otomatik oluşturulur. Bu class daha çok bilgi almak için kullanılır.

### Metodlar

| Metod | Açıklama | Return |
|-------|----------|--------|
| `list_apis()` | REST API'leri listele | List[dict] |
| `get_api_stages(api_id)` | Stage'leri listele | List[dict] |
| `get_endpoint_url(api_id, stage)` | Endpoint URL oluştur | str |

### Kullanım

```python
from aws_toolkit import AWSConfig, APIGatewayOperations

config = AWSConfig().load_from_env()
apigw = APIGatewayOperations(config)

# API'leri listele
apis = apigw.list_apis()
for api in apis:
    print(f"{api['name']} (ID: {api['id']})")

# Endpoint URL al
url = apigw.get_endpoint_url("abc123xyz", "Prod")
# https://abc123xyz.execute-api.eu-central-1.amazonaws.com/Prod
```

---

## ⚡ Yardımcı Fonksiyonlar (Quick Functions)

Tek satırlık işlemler için.

```python
from aws_toolkit import quick_s3_upload, quick_s3_download, quick_lambda_invoke

# Hızlı S3 yükleme
quick_s3_upload("data.json", "data.json", "my-bucket")

# Gzip ile yükleme
quick_s3_upload("large.json", "large.json.gz", "my-bucket", gzip_compress=True)

# Hızlı S3 okuma
content = quick_s3_download("data.json", "my-bucket")
data = json.loads(content)

# Gzip'li okuma
content = quick_s3_download("data.json.gz", "my-bucket", decompress_gzip=True)

# Hızlı Lambda çağrısı
result = quick_lambda_invoke("my-function", {"name": "Kaan"})
```

---

## 🔧 SAM CLI - Serverless Application Model

Lambda + API Gateway deploy etmek için SAM kullanılır.

### Kurulum

```bash
# macOS
brew install aws-sam-cli

# Kontrol
sam --version
```

### Temel Komutlar

```bash
# Proje oluştur
sam init

# Build
sam build

# Local test
sam local invoke MyFunction --event event.json
sam local start-api

# Deploy (ilk kez - guided)
sam deploy --guided

# Deploy (sonraki)
sam deploy

# Logs
sam logs -n MyFunction --tail

# Delete
sam delete
```

### template.yaml Örneği

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: My Lambda API

Globals:
  Function:
    Timeout: 30
    Runtime: python3.9
    MemorySize: 256
    Architectures:
      - arm64

Resources:
  MyFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: handler.lambda_handler
      
      # Ortam değişkenleri
      Environment:
        Variables:
          S3_BUCKET: !Ref S3BucketName
      
      # S3 erişim izni
      Policies:
        - Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - s3:GetObject
                - s3:PutObject
              Resource: !Sub "arn:aws:s3:::${S3BucketName}/*"
      
      # API Gateway event
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /my-endpoint
            Method: get

Outputs:
  ApiUrl:
    Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/"
```

### Lambda Handler Şablonu

```python
import json
import os
import boto3

def lambda_handler(event, context):
    """
    API Gateway'den gelen istekleri işle.
    
    event yapısı:
    {
        "httpMethod": "GET",
        "path": "/my-endpoint",
        "queryStringParameters": {"param1": "value1"},
        "body": null veya JSON string,
        "headers": {...}
    }
    """
    
    # Query parametreleri
    params = event.get("queryStringParameters") or {}
    name = params.get("name", "World")
    
    # Body (POST için)
    body = event.get("body")
    if body:
        data = json.loads(body)
    
    # Response
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"  # CORS
        },
        "body": json.dumps({
            "message": f"Hello, {name}!",
            "source": "Lambda"
        })
    }
```

---

## 🎯 Gerçek Dünya Örnekleri

### Örnek 1: GeoJSON Dosyalarını S3'e Yükleme

```python
from pathlib import Path
from aws_toolkit import AWSConfig, S3Operations
import gzip
import json

config = AWSConfig().load_from_env()
s3 = S3Operations(config, bucket="my-geo-data")

# data/ klasöründeki tüm GeoJSON'ları gzip'le ve yükle
data_dir = Path("data")
for file in data_dir.glob("*.geojson"):
    # Oku
    with open(file) as f:
        content = f.read()
    
    # Sıkıştır
    compressed = gzip.compress(content.encode())
    
    # Yükle
    s3_key = f"tiles/{file.stem}.geojson.gz"
    result = s3.upload_bytes(
        compressed,
        s3_key,
        content_type="application/json"
    )
    
    print(f"✅ {file.name} -> {s3_key}")
```

### Örnek 2: S3'ten Veri Okuyan Lambda

```python
# handler.py
import json
import os
import boto3
import gzip

s3 = boto3.client('s3')
BUCKET = os.environ['S3_BUCKET']

# Memory cache
_cache = {}

def lambda_handler(event, context):
    # Query'den tile ID al
    params = event.get("queryStringParameters") or {}
    tile_id = params.get("tile")
    
    if not tile_id:
        return error_response(400, "tile parameter required")
    
    # Cache kontrol
    if tile_id in _cache:
        data = _cache[tile_id]
    else:
        # S3'ten oku
        try:
            response = s3.get_object(
                Bucket=BUCKET,
                Key=f"tiles/{tile_id}.geojson.gz"
            )
            content = gzip.decompress(response['Body'].read())
            data = json.loads(content)
            _cache[tile_id] = data
        except s3.exceptions.NoSuchKey:
            return error_response(404, f"Tile not found: {tile_id}")
    
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(data)
    }

def error_response(code, message):
    return {
        "statusCode": code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": message})
    }
```

### Örnek 3: Batch İşlem - Çoklu Dosya Yükleme

```python
from concurrent.futures import ThreadPoolExecutor
from aws_toolkit import AWSConfig, S3Operations
from pathlib import Path

config = AWSConfig().load_from_env()
s3 = S3Operations(config, bucket="my-bucket")

def upload_file(file_path: Path):
    """Tek dosya yükle"""
    s3_key = f"uploads/{file_path.name}"
    result = s3.upload_file(file_path, s3_key)
    return result

# 10 thread ile paralel yükleme
files = list(Path("data").glob("*.json"))

with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(upload_file, files))

success = sum(1 for r in results if r["success"])
print(f"✅ {success}/{len(files)} dosya yüklendi")
```

---

## 📊 Maliyet Özeti

| Servis | Free Tier (12 ay) | Sonrası |
|--------|-------------------|---------|
| **S3** | 5 GB storage, 20K GET, 2K PUT | $0.023/GB, $0.0004/1K request |
| **Lambda** | 1M istek, 400K GB-saniye | $0.20/1M istek |
| **API Gateway** | 1M HTTP API çağrısı | $1.00/1M istek |

### Örnek Maliyet Hesabı

```
Senaryo: Ayda 100K API çağrısı, 2GB S3 data

S3:
  Storage: 2GB × $0.023 = $0.05
  GET: 100K × $0.0004 = $0.04
  
Lambda (256MB, ortalama 500ms):
  Compute: 100K × 0.5s × 256MB = 12.5K GB-s
  Free tier içinde = $0
  
API Gateway:
  100K çağrı = $0.10

TOPLAM: ~$0.20/ay
```

---

## 🔍 Troubleshooting

### Credentials Hatası

```python
# Test et
config = AWSConfig().load_from_env()
result = config.test_connection()
print(result)
```

### S3 Access Denied

Lambda'nın IAM policy'sinde S3 izni olduğundan emin ol:

```yaml
Policies:
  - Version: '2012-10-17'
    Statement:
      - Effect: Allow
        Action:
          - s3:GetObject
          - s3:PutObject
        Resource: "arn:aws:s3:::bucket-name/*"
```

### Lambda Timeout

- Memory artır (daha fazla CPU)
- Timeout süresini uzat
- Cold start için provisioned concurrency düşün

### CORS Hatası

Response headers'a ekle:

```python
"headers": {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
}
```

---

## 📚 Faydalı Linkler

- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [S3 User Guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/)

---

*Bu dokümantasyon aws_toolkit.py modülü için hazırlanmıştır.*
