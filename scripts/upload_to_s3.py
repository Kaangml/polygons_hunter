#!/usr/bin/env python3
"""
S3 Yükleme Scripti

Bu script s3_data/ dizinindeki hazırlanmış dosyaları AWS S3'e yükler.

Gereksinimler:
    - .env dosyasında AWS credentials tanımlı olmalı
    - boto3 kütüphanesi yüklü olmalı

Kullanım:
    python scripts/upload_to_s3.py
    python scripts/upload_to_s3.py --create-bucket
    python scripts/upload_to_s3.py --dry-run
"""

import argparse
import os
import sys
from pathlib import Path

# .env dosyasını yükle
def load_env():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())
        print(f"✅ .env dosyası yüklendi: {env_path}")
    else:
        print(f"⚠️  .env dosyası bulunamadı: {env_path}")

load_env()

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    print("❌ boto3 kütüphanesi bulunamadı!")
    print("   Yüklemek için: pip install boto3")
    sys.exit(1)


def create_bucket_if_not_exists(s3_client, bucket_name: str, region: str) -> bool:
    """Bucket yoksa oluştur"""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket zaten mevcut: {bucket_name}")
        return True
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "404":
            print(f"📦 Bucket oluşturuluyor: {bucket_name}")
            try:
                if region == "us-east-1":
                    s3_client.create_bucket(Bucket=bucket_name)
                else:
                    s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={"LocationConstraint": region}
                    )
                print(f"✅ Bucket oluşturuldu: {bucket_name}")
                return True
            except ClientError as create_error:
                print(f"❌ Bucket oluşturulamadı: {create_error}")
                return False
        else:
            print(f"❌ Bucket erişim hatası: {e}")
            return False


def upload_file(s3_client, file_path: Path, bucket: str, s3_key: str, content_type: str = None):
    """Tek dosya yükle"""
    extra_args = {}
    
    if content_type:
        extra_args["ContentType"] = content_type
    
    # Gzip dosyaları için encoding ayarla
    if file_path.suffix == ".gz":
        extra_args["ContentEncoding"] = "gzip"
        extra_args["ContentType"] = "application/geo+json"
    elif file_path.suffix == ".csv":
        extra_args["ContentType"] = "text/csv"
    elif file_path.suffix == ".json":
        extra_args["ContentType"] = "application/json"
    
    s3_client.upload_file(
        str(file_path),
        bucket,
        s3_key,
        ExtraArgs=extra_args if extra_args else None
    )


def upload_to_s3(
    source_dir: str = "s3_data",
    bucket_name: str = "polygons-hunter-data",
    region: str = "eu-central-1",
    create_bucket: bool = False,
    dry_run: bool = False
):
    """
    S3'e dosyaları yükle
    
    Args:
        source_dir: Yüklenecek dosyaların bulunduğu dizin
        bucket_name: Hedef S3 bucket adı
        region: AWS region
        create_bucket: Bucket yoksa oluştur
        dry_run: Sadece ne yapılacağını göster, yükleme yapma
    """
    source_path = Path(source_dir)
    
    if not source_path.exists():
        print(f"❌ Kaynak dizin bulunamadı: {source_path}")
        print("   Önce prepare_s3_data.py scriptini çalıştırın!")
        return False
    
    # Yüklenecek dosyaları bul
    all_files = list(source_path.rglob("*"))
    files_to_upload = [f for f in all_files if f.is_file()]
    
    if not files_to_upload:
        print(f"❌ Yüklenecek dosya bulunamadı: {source_path}")
        return False
    
    print(f"📁 Kaynak dizin: {source_path}")
    print(f"🪣 Hedef bucket: s3://{bucket_name}")
    print(f"🌍 Region: {region}")
    print(f"📊 Toplam dosya: {len(files_to_upload)}")
    
    # Toplam boyut
    total_size = sum(f.stat().st_size for f in files_to_upload)
    print(f"💾 Toplam boyut: {total_size / (1024*1024):.2f} MB")
    print("-" * 50)
    
    if dry_run:
        print("\n🔍 DRY RUN - Yüklenecek dosyalar:")
        for f in files_to_upload[:10]:
            s3_key = str(f.relative_to(source_path))
            print(f"   {f} → s3://{bucket_name}/{s3_key}")
        if len(files_to_upload) > 10:
            print(f"   ... ve {len(files_to_upload) - 10} dosya daha")
        return True
    
    try:
        s3_client = boto3.client("s3", region_name=region)
        
        # Bucket kontrolü
        if create_bucket:
            if not create_bucket_if_not_exists(s3_client, bucket_name, region):
                return False
        else:
            try:
                s3_client.head_bucket(Bucket=bucket_name)
            except ClientError:
                print(f"❌ Bucket bulunamadı: {bucket_name}")
                print("   --create-bucket flag'i ile bucket oluşturabilirsiniz")
                return False
        
        # Dosyaları yükle
        print("\n🚀 Yükleme başlıyor...")
        
        uploaded = 0
        failed = 0
        
        for i, file_path in enumerate(files_to_upload, 1):
            s3_key = str(file_path.relative_to(source_path))
            size_kb = file_path.stat().st_size / 1024
            
            try:
                upload_file(s3_client, file_path, bucket_name, s3_key)
                uploaded += 1
                print(f"[{i:3d}/{len(files_to_upload)}] ✅ {s3_key} ({size_kb:.1f} KB)")
            except Exception as e:
                failed += 1
                print(f"[{i:3d}/{len(files_to_upload)}] ❌ {s3_key} - Hata: {e}")
        
        # Özet
        print("\n" + "=" * 50)
        print("📊 YÜKLEME RAPORU")
        print("=" * 50)
        print(f"✅ Başarılı : {uploaded}")
        print(f"❌ Başarısız: {failed}")
        print(f"🪣 Bucket   : s3://{bucket_name}")
        
        if uploaded > 0:
            print(f"\n🔗 S3 Console: https://s3.console.aws.amazon.com/s3/buckets/{bucket_name}")
        
        return failed == 0
        
    except NoCredentialsError:
        print("❌ AWS kimlik bilgileri bulunamadı!")
        print("   'aws configure' komutunu çalıştırın")
        return False
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="S3'e polygon verilerini yükle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python scripts/upload_to_s3.py
  python scripts/upload_to_s3.py --create-bucket
  python scripts/upload_to_s3.py --dry-run
        """
    )
    
    # .env'den default değerleri al
    default_bucket = os.environ.get("S3_BUCKET_NAME", "polygons-hunter-data")
    default_region = os.environ.get("AWS_DEFAULT_REGION", "eu-central-1")
    
    parser.add_argument(
        "--bucket", "-b",
        default=default_bucket,
        help=f"S3 bucket adı (varsayılan: {default_bucket})"
    )
    
    parser.add_argument(
        "--region", "-r",
        default=default_region,
        help=f"AWS region (varsayılan: {default_region})"
    )
    
    parser.add_argument(
        "--source", "-s",
        default="s3_data",
        help="Kaynak dizin (varsayılan: s3_data)"
    )
    
    parser.add_argument(
        "--create-bucket", "-c",
        action="store_true",
        help="Bucket yoksa oluştur"
    )
    
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Sadece ne yapılacağını göster, yükleme yapma"
    )
    
    args = parser.parse_args()
    
    print("🚀 Polygon Hunter - S3 Yükleme")
    print("=" * 50)
    
    success = upload_to_s3(
        source_dir=args.source,
        bucket_name=args.bucket,
        region=args.region,
        create_bucket=args.create_bucket,
        dry_run=args.dry_run
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
