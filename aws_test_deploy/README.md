# 🎓 AWS Test & Deploy - Öğrenme Ortamı

Bu klasör AWS servislerini öğrenmek ve test etmek için hazırlanmıştır.

## 📁 Yapı

```
aws_test_deploy/
├── README.md
├── config.py                    # AWS credentials yükleme
│
├── s3_bucket/                   # S3 İşlemleri
│   └── 01_s3_basics.ipynb      # S3 temelleri ve CRUD işlemleri
│
├── lambda_api_gateway/          # Lambda & API Gateway
│   ├── 02_lambda_basics.ipynb  # Lambda ve SAM temelleri
│   │
│   ├── hello_world/            # 🎯 EGZERSİZ 1: İlk Lambda'n
│   │   ├── handler.py          # TODO: Sen yazacaksın!
│   │   ├── template.yaml       # TODO: Sen yazacaksın!
│   │   └── README.md           # Talimatlar
│   │
│   └── s3_reader/              # 🎯 EGZERSİZ 2: S3 Okuyan Lambda
│       ├── handler.py          # TODO: Sen yazacaksın!
│       ├── template.yaml       # TODO: Sen yazacaksın!
│       └── README.md           # Talimatlar
│
└── solutions/                   # ⚠️ ÇÖZÜMLER (Önce kendin dene!)
    ├── hello_world_handler.py
    ├── hello_world_template.yaml
    ├── s3_reader_handler.py
    └── s3_reader_template.yaml
```

## 🚀 Başlangıç

### 1. Önce Notebook'ları İncele
1. `s3_bucket/01_s3_basics.ipynb` - S3 temellerini öğren
2. `lambda_api_gateway/02_lambda_basics.ipynb` - Lambda kavramlarını anla

### 2. Sonra Egzersizleri Yap
1. `lambda_api_gateway/hello_world/` - İlk Lambda'nı yaz
2. `lambda_api_gateway/s3_reader/` - S3'ten okuyan Lambda yaz

### 3. Takılırsan Çözümlere Bak
`solutions/` klasöründe çözümler var - ama önce kendin dene!

## 🎯 Öğrenme Hedefleri

### S3
- [ ] Bucket oluşturma/silme
- [ ] Dosya yükleme/indirme
- [ ] Dosya listeleme
- [ ] Dosya silme

### Lambda + API Gateway
- [ ] Hello World Lambda yazma
- [ ] SAM template anlama
- [ ] Deploy işlemi
- [ ] API Gateway endpoint kullanma
- [ ] S3'ten veri okuyan Lambda yazma

## 💰 Maliyet Bilgisi

| Servis | Free Tier | Sonrası |
|--------|-----------|---------|
| S3 | 5GB/ay, 20K GET | $0.023/GB |
| Lambda | 1M istek, 400K GB-s | $0.20/1M istek |
| API Gateway | 1M HTTP istek | $1/1M istek |

> ⚠️ Free Tier 12 ay geçerli. Test için endişe etme!

## 📝 Egzersiz Sıralaması

1. **01_s3_basics.ipynb** - S3 işlemlerini test et
2. **02_lambda_basics.ipynb** - Lambda kavramlarını oku
3. **hello_world/** - İlk Lambda'nı yaz ve deploy et
4. **s3_reader/** - S3 okuyan Lambda yaz ve deploy et
5. **Ana proje**: `aws_lambda/` klasörüne dön ve gerçek projeyi anla!
