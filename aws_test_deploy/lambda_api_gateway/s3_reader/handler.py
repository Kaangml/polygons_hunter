"""
S3 Reader Lambda Handler - SEN YAZACAKSIN!

Bu dosyada S3'ten veri okuyan bir Lambda fonksiyonu yazacaksın.
API Gateway isteği alır, S3'ten dosya okur ve JSON response döner.

GÖREV:
1. lambda_handler fonksiyonunu tamamla
2. boto3 ile S3'e bağlan
3. Belirtilen dosyayı oku ve içeriğini döndür

ORTAM DEĞİŞKENLERİ (template.yaml'da tanımlanacak):
- S3_BUCKET: Bucket adı

API Gateway Request:
GET /file?key=test.json

Lambda Response:
{
    "statusCode": 200,
    "body": "{\"file_content\": {...}, \"file_key\": \"test.json\"}"
}

İPUÇLARI:
- boto3.client('s3') ile S3 client oluştur
- os.environ['S3_BUCKET'] ile ortam değişkenini oku
- s3.get_object(Bucket=bucket, Key=key) ile dosya oku
- response['Body'].read().decode('utf-8') ile içeriği string yap
- Hata durumunda try/except kullan
"""

import json
import os
# TODO: boto3'ü import et


def lambda_handler(event, context):
    """
    S3'ten dosya okuyan Lambda handler.
    
    Args:
        event: API Gateway request
        context: Lambda runtime context
    
    Returns:
        dict: API Gateway response
    """
    
    # TODO 1: Ortam değişkeninden bucket adını al
    # İpucu: os.environ.get("S3_BUCKET") veya os.environ["S3_BUCKET"]
    
    bucket = # SENİN KODUN
    
    # TODO 2: Query parametresinden dosya key'ini al
    # Varsayılan olarak "index.json" kullan
    
    query_params = event.get("queryStringParameters") or {}
    file_key = # SENİN KODUN - query_params'tan "key" al, yoksa "index.json"
    
    # TODO 3: S3 client oluştur
    
    s3_client = # SENİN KODUN - boto3.client kullan
    
    # TODO 4: Dosyayı S3'ten oku
    # Hata durumunda uygun response döndür
    
    try:
        # S3'ten dosyayı al
        response = # SENİN KODUN - s3_client.get_object kullan
        
        # Body'yi oku ve decode et
        file_content = # SENİN KODUN - response['Body'].read().decode('utf-8')
        
        # JSON ise parse et
        try:
            file_data = json.loads(file_content)
        except json.JSONDecodeError:
            file_data = file_content  # JSON değilse string olarak bırak
        
        # TODO 5: Başarılı response döndür
        return {
            "statusCode": # SENİN KODUN,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "file_key": file_key,
                "bucket": bucket,
                "content": file_data
            })
        }
        
    except Exception as e:
        # TODO 6: Hata response'u döndür
        return {
            "statusCode": # SENİN KODUN - hangi status code?
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": str(e),
                "file_key": file_key,
                "bucket": bucket
            })
        }


# Local test için (S3'e erişim gerektirir)
if __name__ == "__main__":
    # Ortam değişkenini set et
    os.environ["S3_BUCKET"] = "polygons-hunter-data"
    
    # Test event
    test_event = {
        "httpMethod": "GET",
        "path": "/file",
        "queryStringParameters": {"key": "index.json"},
        "body": None
    }
    
    # Handler'ı çağır
    response = lambda_handler(test_event, None)
    
    print("Response:")
    print(json.dumps(response, indent=2))
