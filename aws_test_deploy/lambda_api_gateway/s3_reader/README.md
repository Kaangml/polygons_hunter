# S3 Reader Lambda - Egzersiz

## 🎯 Amaç
S3'ten dosya okuyan bir Lambda fonksiyonu yazıp deploy etmek.

## 📁 Dosyalar

1. **handler.py** - Lambda fonksiyon kodu (SEN YAZACAKSIN)
2. **template.yaml** - SAM CloudFormation template (SEN YAZACAKSIN)

## 🔧 Yapılacaklar

### Adım 1: handler.py'yi tamamla
- boto3 ile S3 client oluştur
- Ortam değişkeninden bucket adını oku
- S3'ten dosya içeriğini oku
- Hata yönetimi ekle

### Adım 2: template.yaml'ı tamamla
- Ortam değişkenlerini tanımla (Environment)
- IAM Policy ekle (S3 erişim izni)
- API Gateway event'i tanımla

### Adım 3: Local test et
```bash
cd aws_test_deploy/lambda_api_gateway/s3_reader
python handler.py
```

### Adım 4: SAM ile deploy et
```bash
sam build
sam deploy --guided
```

## 💡 Önemli Kavramlar

### Ortam Değişkenleri
```yaml
# template.yaml
Environment:
  Variables:
    S3_BUCKET: !Ref S3BucketName
```

```python
# handler.py
bucket = os.environ["S3_BUCKET"]
```

### IAM Policy (S3 Erişimi)
```yaml
Policies:
  - Version: '2012-10-17'
    Statement:
      - Effect: Allow
        Action:
          - s3:GetObject
        Resource:
          - !Sub "arn:aws:s3:::${S3BucketName}/*"
```

### S3'ten Dosya Okuma
```python
import boto3

s3 = boto3.client('s3')
response = s3.get_object(Bucket=bucket, Key=file_key)
content = response['Body'].read().decode('utf-8')
```

## ⚠️ Dikkat Edilecekler

1. **IAM Policy zorunlu!** - Lambda varsayılan olarak S3'e erişemez
2. **Ortam değişkenleri** - Hardcode yerine Environment kullan
3. **Hata yönetimi** - Dosya bulunamazsa 404 döndür
4. **CORS** - Frontend erişimi için gerekli

## ✅ Başarı Kriterleri

1. [ ] handler.py boto3 ile S3'e bağlanıyor
2. [ ] Ortam değişkeni doğru okunuyor
3. [ ] S3'ten dosya okunabiliyor
4. [ ] Hata durumunda uygun response dönüyor
5. [ ] Deploy sonrası API çalışıyor

## 🔗 Bu Egzersizden Sonra
Ana projemiz olan `aws_lambda/` klasöründeki kodu inceleyebilirsin!
Bu egzersizler, ana projedeki yapıyı anlamana yardımcı olacak.
