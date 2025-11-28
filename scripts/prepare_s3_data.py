#!/usr/bin/env python3
"""
S3 Veri Hazırlığı Scripti

Bu script:
1. data2/ içindeki tüm GeoJSON dosyalarını okur
2. Her birini gzip formatında sıkıştırır
3. S3 için optimize edilmiş quadkey_index.csv oluşturur

Kullanım:
    python scripts/prepare_s3_data.py

Çıktı:
    s3_data/
    ├── index/
    │   └── quadkey_index.csv
    └── tiles/
        ├── 120322312.geojson.gz
        ├── 120322321.geojson.gz
        └── ...
"""

import gzip
import json
import csv
import os
from pathlib import Path
from datetime import datetime


def get_file_size(filepath: Path) -> int:
    """Dosya boyutunu byte cinsinden döndür"""
    return filepath.stat().st_size


def count_polygons(geojson_data: dict) -> int:
    """GeoJSON içindeki polygon sayısını hesapla"""
    count = 0
    features = geojson_data.get("features", [])
    for feature in features:
        geometry = feature.get("geometry", {})
        geom_type = geometry.get("type", "")
        if geom_type in ("Polygon", "MultiPolygon"):
            count += 1
        elif geom_type == "GeometryCollection":
            for geom in geometry.get("geometries", []):
                if geom.get("type") in ("Polygon", "MultiPolygon"):
                    count += 1
                    break
    return count


def extract_quadkey_from_filename(filename: str) -> str:
    """Dosya adından quadkey'i çıkar (örn: 120322312.geojson -> 120322312)"""
    return Path(filename).stem


def prepare_s3_data(
    input_dir: str = "data2",
    output_dir: str = "s3_data",
    compress: bool = True
):
    """
    GeoJSON dosyalarını S3 için hazırla
    
    Args:
        input_dir: Kaynak GeoJSON dosyalarının bulunduğu dizin
        output_dir: Çıktı dizini
        compress: Gzip sıkıştırma uygula
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Çıktı dizinlerini oluştur
    tiles_dir = output_path / "tiles"
    index_dir = output_path / "index"
    tiles_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Kaynak dizin: {input_path}")
    print(f"📦 Çıktı dizini: {output_path}")
    print(f"🗜️  Gzip sıkıştırma: {'Evet' if compress else 'Hayır'}")
    print("-" * 50)
    
    # GeoJSON dosyalarını bul
    geojson_files = sorted(input_path.glob("*.geojson"))
    total_files = len(geojson_files)
    
    if total_files == 0:
        print(f"❌ {input_path} dizininde GeoJSON dosyası bulunamadı!")
        return
    
    print(f"📊 Toplam {total_files} GeoJSON dosyası bulundu\n")
    
    # Index verileri
    index_data = []
    
    # İstatistikler
    total_original_size = 0
    total_compressed_size = 0
    total_polygons = 0
    
    # Her dosyayı işle
    for i, geojson_file in enumerate(geojson_files, 1):
        quadkey = extract_quadkey_from_filename(geojson_file.name)
        original_size = get_file_size(geojson_file)
        total_original_size += original_size
        
        # GeoJSON'ı oku
        with open(geojson_file, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)
        
        polygon_count = count_polygons(geojson_data)
        total_polygons += polygon_count
        
        # Çıktı dosya adı
        if compress:
            output_filename = f"{quadkey}.geojson.gz"
            output_file = tiles_dir / output_filename
            
            # Gzip olarak kaydet
            json_bytes = json.dumps(geojson_data, separators=(",", ":")).encode("utf-8")
            with gzip.open(output_file, "wb", compresslevel=9) as f:
                f.write(json_bytes)
        else:
            output_filename = f"{quadkey}.geojson"
            output_file = tiles_dir / output_filename
            
            # Normal JSON olarak kaydet
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(geojson_data, f, separators=(",", ":"))
        
        compressed_size = get_file_size(output_file)
        total_compressed_size += compressed_size
        
        # Sıkıştırma oranı
        compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        
        # Index'e ekle
        index_data.append({
            "quadkey": quadkey,
            "s3_path": f"tiles/{output_filename}",
            "polygon_count": polygon_count,
            "original_size_bytes": original_size,
            "compressed_size_bytes": compressed_size,
            "compression_ratio": round(compression_ratio, 1)
        })
        
        # İlerleme göster
        progress = (i / total_files) * 100
        size_mb = original_size / (1024 * 1024)
        comp_mb = compressed_size / (1024 * 1024)
        
        print(f"[{i:3d}/{total_files}] {quadkey} | "
              f"{size_mb:.2f}MB → {comp_mb:.2f}MB ({compression_ratio:.1f}% küçülme) | "
              f"{polygon_count:,} polygon")
    
    # Index CSV'yi oluştur
    index_file = index_dir / "quadkey_index.csv"
    with open(index_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "quadkey", "s3_path", "polygon_count", 
            "original_size_bytes", "compressed_size_bytes", "compression_ratio"
        ])
        writer.writeheader()
        writer.writerows(index_data)
    
    # Özet
    print("\n" + "=" * 50)
    print("📊 ÖZET RAPOR")
    print("=" * 50)
    print(f"✅ İşlenen dosya sayısı  : {total_files}")
    print(f"📍 Toplam polygon sayısı : {total_polygons:,}")
    print(f"📁 Orijinal boyut       : {total_original_size / (1024*1024):.2f} MB")
    print(f"🗜️  Sıkıştırılmış boyut  : {total_compressed_size / (1024*1024):.2f} MB")
    print(f"📉 Toplam küçülme       : {(1 - total_compressed_size/total_original_size)*100:.1f}%")
    print(f"\n📄 Index dosyası: {index_file}")
    print(f"📦 Tile dosyaları: {tiles_dir}/")
    
    # S3 upload komutu
    print("\n" + "=" * 50)
    print("🚀 S3'E YÜKLEMEK İÇİN:")
    print("=" * 50)
    print(f"aws s3 sync {output_path}/ s3://polygons-hunter-data/")
    
    return index_data


if __name__ == "__main__":
    print("🚀 Polygon Hunter - S3 Veri Hazırlığı")
    print(f"⏰ Başlangıç: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50 + "\n")
    
    prepare_s3_data()
    
    print(f"\n⏰ Bitiş: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("✅ İşlem tamamlandı!")
