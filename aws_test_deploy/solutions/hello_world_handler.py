"""
Hello World Lambda Handler - ÇÖZÜM
"""

import json


def lambda_handler(event, context):
    """
    Lambda handler fonksiyonu.
    """
    
    # Query parametrelerini al
    query_params = event.get("queryStringParameters")
    
    if query_params and "name" in query_params:
        name = query_params["name"]
    else:
        name = "World"
    
    # Response body'sini oluştur
    response_body = {
        "message": f"Hello, {name}!",
        "source": "Lambda"
    }
    
    # Lambda response'unu döndür
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(response_body)
    }


# Local test için
if __name__ == "__main__":
    test_event = {
        "httpMethod": "GET",
        "path": "/hello",
        "queryStringParameters": {"name": "Kaan"},
        "body": None,
        "headers": {}
    }
    
    response = lambda_handler(test_event, None)
    
    print("Response:")
    print(json.dumps(response, indent=2))
