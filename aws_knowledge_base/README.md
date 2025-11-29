# AWS Knowledge Base

Bu klasör AWS servislerini (S3, Lambda, API Gateway, SAM) kullanmak için hazırlanmış bir toolkit ve dokümantasyon içerir.

## 📁 Dosyalar

| Dosya | Açıklama |
|-------|----------|
| `aws_toolkit.py` | AWS işlemleri için Python modülü |
| `AWS_TOOLKIT_DOCS.md` | Kapsamlı dokümantasyon |

## 🚀 Hızlı Kullanım

```python
from aws_toolkit import AWSConfig, S3Operations, LambdaOperations

# 1. Konfigürasyon
config = AWSConfig().load_from_env()

# 2. S3 işlemleri
s3 = S3Operations(config, bucket="my-bucket")
s3.upload_file("local.json", "remote.json")
content = s3.get_object("remote.json")

# 3. Lambda işlemleri
lam = LambdaOperations(config)
result = lam.invoke("my-function", {"key": "value"})
```

## 📋 Gereksinimler

```bash
pip install boto3
```

## 🔧 .env Dosyası

```env
AWS_ACCESS_KEY_ID=AKIAXXXXXXXX
AWS_SECRET_ACCESS_KEY=xxxxxxxx
AWS_REGION=eu-central-1
S3_BUCKET=my-bucket
```

## 📚 Detaylı Dokümantasyon

`AWS_TOOLKIT_DOCS.md` dosyasında:
- Her fonksiyonun detaylı açıklaması
- Kullanım örnekleri
- SAM CLI komutları
- Gerçek dünya örnekleri
- Maliyet bilgileri
- Troubleshooting

## 🎯 İçerik

### Classes

1. **AWSConfig** - Credentials ve client yönetimi
2. **S3Operations** - Bucket ve object işlemleri
3. **LambdaOperations** - Lambda fonksiyon yönetimi
4. **APIGatewayOperations** - API Gateway bilgileri

### Quick Functions

- `quick_s3_upload()` - Tek satırda dosya yükle
- `quick_s3_download()` - Tek satırda dosya oku
- `quick_lambda_invoke()` - Tek satırda Lambda çağır

---

*Bu klasörü ayrı bir repo olarak kullanabilirsin!*
