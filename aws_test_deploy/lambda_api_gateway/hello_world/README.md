# Hello World Lambda - Egzersiz

## 🎯 Amaç
Basit bir "Hello World" Lambda fonksiyonu yazıp deploy etmek.

## 📁 Dosyalar

1. **handler.py** - Lambda fonksiyon kodu (SEN YAZACAKSIN)
2. **template.yaml** - SAM CloudFormation template (SEN YAZACAKSIN)

## 🔧 Yapılacaklar

### Adım 1: handler.py'yi tamamla
- `lambda_handler` fonksiyonunu yaz
- Event'ten query parametrelerini oku
- JSON response döndür

### Adım 2: template.yaml'ı tamamla
- Runtime, timeout, memory ayarla
- Handler path'ini doğru yaz
- API Gateway event'i tanımla

### Adım 3: Local test et
```bash
cd aws_test_deploy/lambda_api_gateway/hello_world
python handler.py
```

### Adım 4: SAM ile deploy et
```bash
# Build
sam build

# Deploy (guided)
sam deploy --guided
```

## 💡 İpuçları

### Lambda Response Formatı
```python
{
    "statusCode": 200,
    "headers": {"Content-Type": "application/json"},
    "body": json.dumps({"message": "Hello!"})  # STRING!
}
```

### Event'ten Parametre Okuma
```python
# queryStringParameters None olabilir!
params = event.get("queryStringParameters") or {}
name = params.get("name", "World")
```

## ✅ Başarı Kriterleri

1. [ ] handler.py syntax hatası olmadan çalışıyor
2. [ ] Local test başarılı
3. [ ] SAM build başarılı
4. [ ] Deploy sonrası API çalışıyor
5. [ ] ?name=Kaan ile "Hello, Kaan!" dönüyor

## 🔗 Sonraki Adım
s3_reader/ klasöründeki egzersizi yap!
