"""
Hello World Lambda Handler - SEN YAZACAKSIN!

Bu dosyada basit bir Lambda fonksiyonu yazacaksın.
Lambda fonksiyonu, bir API Gateway isteği alır ve JSON response döner.

GÖREV:
1. lambda_handler fonksiyonunu tamamla
2. API Gateway'den gelen event'i anla
3. Düzgün bir JSON response döndür

API Gateway Event Yapısı:
{
    "httpMethod": "GET",
    "path": "/hello",
    "queryStringParameters": {"name": "Kaan"},  # veya None
    "body": null,  # POST için string olabilir
    "headers": {...}
}

Lambda Response Yapısı:
{
    "statusCode": 200,
    "headers": {"Content-Type": "application/json"},
    "body": "{\"message\": \"Hello World\"}"  # JSON STRING olmalı!
}

İPUÇLARI:
- body her zaman JSON string olmalı, dict değil!
- json.dumps() kullanarak dict'i string'e çevir
- queryStringParameters None olabilir, kontrol et
"""

import json


def lambda_handler(event, context):
    """
    Lambda handler fonksiyonu.
    
    Args:
        event: API Gateway'den gelen request
        context: Lambda runtime bilgileri (kullanmayacağız şimdilik)
    
    Returns:
        dict: API Gateway response formatında dict
    """
    
    # TODO 1: event'ten query parametrelerini al
    # Eğer "name" parametresi varsa onu kullan, yoksa "World" kullan
    # İpucu: event.get("queryStringParameters") kullan
    # Dikkat: queryStringParameters None olabilir!
    
    query_params = # SENİN KODUN
    
    if query_params and "name" in query_params:
        name = # SENİN KODUN
    else:
        name = "World"
    
    # TODO 2: Response body'sini oluştur
    # {"message": "Hello, {name}!", "source": "Lambda"}
    
    response_body = # SENİN KODUN - dict olarak oluştur
    
    # TODO 3: Lambda response'unu döndür
    # statusCode, headers ve body içermeli
    # body JSON STRING olmalı!
    
    return {
        "statusCode": # SENİN KODUN,
        "headers": {
            # SENİN KODUN - Content-Type header ekle
        },
        "body": # SENİN KODUN - json.dumps() kullan!
    }


# Local test için
if __name__ == "__main__":
    # Test event - API Gateway formatında
    test_event = {
        "httpMethod": "GET",
        "path": "/hello",
        "queryStringParameters": {"name": "Kaan"},
        "body": None,
        "headers": {}
    }
    
    # Handler'ı çağır
    response = lambda_handler(test_event, None)
    
    print("Response:")
    print(json.dumps(response, indent=2))
    
    # Beklenen çıktı:
    # {
    #   "statusCode": 200,
    #   "headers": {"Content-Type": "application/json"},
    #   "body": "{\"message\": \"Hello, Kaan!\", \"source\": \"Lambda\"}"
    # }
