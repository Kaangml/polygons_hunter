"""
S3 Reader Lambda Handler - ÇÖZÜM
"""

import json
import os
import boto3


def lambda_handler(event, context):
    """
    S3'ten dosya okuyan Lambda handler.
    """
    
    # Ortam değişkeninden bucket adını al
    bucket = os.environ.get("S3_BUCKET", "polygons-hunter-data")
    
    # Query parametresinden dosya key'ini al
    query_params = event.get("queryStringParameters") or {}
    file_key = query_params.get("key", "index.json")
    
    # S3 client oluştur
    s3_client = boto3.client('s3')
    
    try:
        # S3'ten dosyayı al
        response = s3_client.get_object(Bucket=bucket, Key=file_key)
        
        # Body'yi oku ve decode et
        file_content = response['Body'].read().decode('utf-8')
        
        # JSON ise parse et
        try:
            file_data = json.loads(file_content)
        except json.JSONDecodeError:
            file_data = file_content
        
        # Başarılı response döndür
        return {
            "statusCode": 200,
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
        
    except s3_client.exceptions.NoSuchKey:
        return {
            "statusCode": 404,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": f"File not found: {file_key}",
                "bucket": bucket
            })
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": str(e),
                "file_key": file_key,
                "bucket": bucket
            })
        }


# Local test için
if __name__ == "__main__":
    os.environ["S3_BUCKET"] = "polygons-hunter-data"
    
    test_event = {
        "httpMethod": "GET",
        "path": "/file",
        "queryStringParameters": {"key": "index.json"},
        "body": None
    }
    
    response = lambda_handler(test_event, None)
    
    print("Response:")
    print(json.dumps(response, indent=2))
