"""
AWS Lambda Handler with Mangum.

Bu dosya Lambda'nın entry point'idir.
Mangum, FastAPI'yi Lambda ile uyumlu hale getirir.
"""

from mangum import Mangum
from app import app


# Lambda handler
handler = Mangum(app, lifespan="off")


# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
