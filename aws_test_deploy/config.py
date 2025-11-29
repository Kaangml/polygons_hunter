"""
AWS Configuration Module
========================
Bu dosya .env'den AWS credentials'ları yükler ve boto3 client'ları oluşturur.

Kullanım:
    from config import get_s3_client, get_lambda_client, AWS_REGION, S3_BUCKET
"""

import os
from pathlib import Path
from functools import lru_cache

# .env dosyasını yükle
def load_env():
    """
    .env dosyasından environment variables yükle.
    
    .env formatı:
        AWS_ACCESS_KEY_ID=AKIA...
        AWS_SECRET_ACCESS_KEY=abc123...
        AWS_DEFAULT_REGION=eu-central-1
    """
    # Proje root'una göre .env bul
    env_path = Path(__file__).parent.parent / ".env"
    
    if not env_path.exists():
        print(f"⚠️  .env dosyası bulunamadı: {env_path}")
        print("   Lütfen .env dosyası oluşturun!")
        return False
    
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            # Boş satır ve yorumları atla
            if not line or line.startswith("#"):
                continue
            # Key=Value formatını parse et
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())
    
    print(f"✅ .env dosyası yüklendi: {env_path}")
    return True

# Modül yüklendiğinde .env'i yükle
load_env()

# ============================================
# Environment Variables
# ============================================
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "eu-central-1")
S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "polygons-hunter-data")

# ============================================
# Boto3 Client Factory
# ============================================
# lru_cache ile client'ları cache'le - her seferinde yeni oluşturma
@lru_cache(maxsize=1)
def get_s3_client():
    """
    S3 client döndür.
    
    Returns:
        boto3.client: S3 client instance
        
    Örnek:
        s3 = get_s3_client()
        s3.list_buckets()
    """
    import boto3
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

@lru_cache(maxsize=1)
def get_lambda_client():
    """
    Lambda client döndür.
    
    Returns:
        boto3.client: Lambda client instance
    """
    import boto3
    return boto3.client(
        "lambda",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

@lru_cache(maxsize=1)
def get_iam_client():
    """
    IAM client döndür.
    
    Returns:
        boto3.client: IAM client instance
    """
    import boto3
    return boto3.client(
        "iam",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

# ============================================
# Credential Validation
# ============================================
def validate_credentials():
    """
    AWS credentials'ları doğrula.
    
    Returns:
        bool: Credentials geçerli mi?
    """
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        print("❌ AWS credentials eksik!")
        print("   AWS_ACCESS_KEY_ID ve AWS_SECRET_ACCESS_KEY tanımlı olmalı")
        return False
    
    try:
        s3 = get_s3_client()
        s3.list_buckets()
        print("✅ AWS credentials geçerli!")
        print(f"   Region: {AWS_REGION}")
        print(f"   Access Key: {AWS_ACCESS_KEY_ID[:10]}...")
        return True
    except Exception as e:
        print(f"❌ AWS bağlantı hatası: {e}")
        return False

# ============================================
# Quick Info
# ============================================
def print_config():
    """Mevcut konfigürasyonu göster."""
    print("=" * 50)
    print("📋 AWS Konfigürasyonu")
    print("=" * 50)
    print(f"Region      : {AWS_REGION}")
    print(f"Access Key  : {AWS_ACCESS_KEY_ID[:10] if AWS_ACCESS_KEY_ID else 'YOK'}...")
    print(f"S3 Bucket   : {S3_BUCKET}")
    print("=" * 50)

# Bu dosya direkt çalıştırılırsa test et
if __name__ == "__main__":
    print_config()
    validate_credentials()
