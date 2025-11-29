"""
AWS Toolkit - S3, Lambda, API Gateway, SAM İşlemleri

Bu modül AWS servislerini kullanmak için hazır fonksiyonlar sağlar.
Her fonksiyon docstring ile detaylı açıklanmıştır.

Kullanım:
    from aws_toolkit import AWSConfig, S3Operations, LambdaOperations

Gereksinimler:
    pip install boto3 python-dotenv

Ortam Değişkenleri (.env):
    AWS_ACCESS_KEY_ID=your_access_key
    AWS_SECRET_ACCESS_KEY=your_secret_key
    AWS_REGION=eu-central-1
    S3_BUCKET=your-bucket-name
"""

import os
import json
import gzip
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from io import BytesIO

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    raise ImportError("boto3 gerekli: pip install boto3")


# =============================================================================
# BÖLÜM 1: KONFIGÜRASYON
# =============================================================================

class AWSConfig:
    """
    AWS Konfigürasyon Yöneticisi
    
    .env dosyasından veya ortam değişkenlerinden AWS credentials yükler.
    
    Kullanım:
        config = AWSConfig()
        config.load_from_env()  # .env dosyasından yükle
        
        # Veya doğrudan değerlerle
        config = AWSConfig(
            access_key="AKIA...",
            secret_key="...",
            region="eu-central-1"
        )
    """
    
    def __init__(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: str = "eu-central-1",
        bucket: Optional[str] = None
    ):
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.bucket = bucket
        self._session = None
    
    def load_from_env(self, env_path: Optional[str] = None) -> "AWSConfig":
        """
        .env dosyasından credentials yükle.
        
        Args:
            env_path: .env dosya yolu. None ise cwd'de arar.
        
        Returns:
            self (chaining için)
        
        Örnek .env:
            AWS_ACCESS_KEY_ID=AKIAXXXXXXXX
            AWS_SECRET_ACCESS_KEY=xxxxx
            AWS_REGION=eu-central-1
            S3_BUCKET=my-bucket
        """
        if env_path is None:
            env_path = Path.cwd() / ".env"
        else:
            env_path = Path(env_path)
        
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ.setdefault(key.strip(), value.strip())
        
        self.access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        self.secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.region = os.environ.get("AWS_REGION", "eu-central-1")
        self.bucket = os.environ.get("S3_BUCKET")
        
        return self
    
    def validate(self) -> bool:
        """Credentials'ların dolu olup olmadığını kontrol et."""
        return all([self.access_key, self.secret_key, self.region])
    
    @property
    def session(self) -> boto3.Session:
        """Boto3 session objesi döndür (lazy loading)."""
        if self._session is None:
            self._session = boto3.Session(
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
        return self._session
    
    def get_client(self, service: str):
        """
        Belirtilen AWS servisi için client oluştur.
        
        Args:
            service: 's3', 'lambda', 'apigateway', 'iam', 'sts' vb.
        
        Returns:
            boto3 client
        
        Örnek:
            s3 = config.get_client('s3')
            lambda_client = config.get_client('lambda')
        """
        return self.session.client(service)
    
    def get_resource(self, service: str):
        """
        Belirtilen AWS servisi için resource oluştur.
        
        Args:
            service: 's3' vb. (resource destekleyen servisler)
        
        Returns:
            boto3 resource
        
        Örnek:
            s3_resource = config.get_resource('s3')
            bucket = s3_resource.Bucket('my-bucket')
        """
        return self.session.resource(service)
    
    def test_connection(self) -> Dict[str, Any]:
        """
        AWS bağlantısını test et.
        
        Returns:
            dict: Bağlantı durumu ve account bilgileri
        
        Örnek:
            result = config.test_connection()
            if result['success']:
                print(f"Account: {result['account_id']}")
        """
        try:
            sts = self.get_client('sts')
            identity = sts.get_caller_identity()
            return {
                "success": True,
                "account_id": identity["Account"],
                "user_arn": identity["Arn"],
                "user_id": identity["UserId"]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# =============================================================================
# BÖLÜM 2: S3 İŞLEMLERİ
# =============================================================================

class S3Operations:
    """
    S3 Bucket ve Object İşlemleri
    
    Kullanım:
        config = AWSConfig().load_from_env()
        s3 = S3Operations(config)
        
        # Bucket işlemleri
        s3.create_bucket("my-bucket")
        s3.list_buckets()
        
        # Object işlemleri
        s3.upload_file("local.txt", "remote.txt")
        s3.download_file("remote.txt", "local.txt")
    """
    
    def __init__(self, config: AWSConfig, bucket: Optional[str] = None):
        """
        Args:
            config: AWSConfig instance
            bucket: Varsayılan bucket adı (opsiyonel)
        """
        self.config = config
        self.bucket = bucket or config.bucket
        self._client = None
        self._resource = None
    
    @property
    def client(self):
        """S3 client (lazy loading)."""
        if self._client is None:
            self._client = self.config.get_client('s3')
        return self._client
    
    @property
    def resource(self):
        """S3 resource (lazy loading)."""
        if self._resource is None:
            self._resource = self.config.get_resource('s3')
        return self._resource
    
    # -------------------------------------------------------------------------
    # BUCKET İŞLEMLERİ
    # -------------------------------------------------------------------------
    
    def list_buckets(self) -> List[Dict[str, Any]]:
        """
        Tüm bucket'ları listele.
        
        Returns:
            List[dict]: Her bucket için {name, creation_date}
        
        Örnek:
            buckets = s3.list_buckets()
            for b in buckets:
                print(f"{b['name']} - {b['creation_date']}")
        """
        response = self.client.list_buckets()
        return [
            {
                "name": b["Name"],
                "creation_date": b["CreationDate"].isoformat()
            }
            for b in response.get("Buckets", [])
        ]
    
    def bucket_exists(self, bucket: Optional[str] = None) -> bool:
        """
        Bucket'ın var olup olmadığını kontrol et.
        
        Args:
            bucket: Bucket adı (None ise varsayılan kullanılır)
        
        Returns:
            bool: Bucket varsa True
        """
        bucket = bucket or self.bucket
        try:
            self.client.head_bucket(Bucket=bucket)
            return True
        except ClientError:
            return False
    
    def create_bucket(
        self,
        bucket: Optional[str] = None,
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Yeni bucket oluştur.
        
        Args:
            bucket: Bucket adı
            region: AWS region (None ise config'den alınır)
        
        Returns:
            dict: {success, bucket, location}
        
        Örnek:
            result = s3.create_bucket("my-new-bucket")
            if result['success']:
                print(f"Bucket oluşturuldu: {result['location']}")
        
        Not:
            - Bucket adları global olarak unique olmalı
            - Küçük harf, tire ve rakam kullanılabilir
            - 3-63 karakter uzunluğunda olmalı
        """
        bucket = bucket or self.bucket
        region = region or self.config.region
        
        try:
            # us-east-1 için LocationConstraint belirtilmez
            if region == "us-east-1":
                self.client.create_bucket(Bucket=bucket)
            else:
                self.client.create_bucket(
                    Bucket=bucket,
                    CreateBucketConfiguration={"LocationConstraint": region}
                )
            
            return {
                "success": True,
                "bucket": bucket,
                "location": f"s3://{bucket}"
            }
        except ClientError as e:
            return {"success": False, "error": str(e)}
    
    def delete_bucket(self, bucket: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        """
        Bucket'ı sil.
        
        Args:
            bucket: Bucket adı
            force: True ise önce içindekileri sil
        
        Returns:
            dict: {success, message}
        
        Örnek:
            # Boş bucket sil
            s3.delete_bucket("my-bucket")
            
            # İçindekilerle birlikte sil
            s3.delete_bucket("my-bucket", force=True)
        
        Uyarı:
            force=True ile tüm objeler kalıcı olarak silinir!
        """
        bucket = bucket or self.bucket
        
        try:
            if force:
                # Önce tüm objeleri sil
                bucket_resource = self.resource.Bucket(bucket)
                bucket_resource.objects.all().delete()
            
            self.client.delete_bucket(Bucket=bucket)
            return {"success": True, "message": f"Bucket silindi: {bucket}"}
        except ClientError as e:
            return {"success": False, "error": str(e)}
    
    # -------------------------------------------------------------------------
    # OBJECT İŞLEMLERİ
    # -------------------------------------------------------------------------
    
    def list_objects(
        self,
        prefix: str = "",
        bucket: Optional[str] = None,
        max_keys: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Bucket içindeki objeleri listele.
        
        Args:
            prefix: Filtre için prefix (klasör gibi)
            bucket: Bucket adı
            max_keys: Maksimum obje sayısı
        
        Returns:
            List[dict]: Her obje için {key, size, last_modified}
        
        Örnek:
            # Tüm objeler
            objects = s3.list_objects()
            
            # Sadece tiles/ altındakiler
            objects = s3.list_objects(prefix="tiles/")
            
            for obj in objects:
                print(f"{obj['key']} - {obj['size']} bytes")
        """
        bucket = bucket or self.bucket
        
        response = self.client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix,
            MaxKeys=max_keys
        )
        
        return [
            {
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat()
            }
            for obj in response.get("Contents", [])
        ]
    
    def upload_file(
        self,
        local_path: Union[str, Path],
        s3_key: str,
        bucket: Optional[str] = None,
        content_type: Optional[str] = None,
        content_encoding: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Dosyayı S3'e yükle.
        
        Args:
            local_path: Lokal dosya yolu
            s3_key: S3'teki key (dosya adı/yolu)
            bucket: Bucket adı
            content_type: MIME type (örn: 'application/json')
            content_encoding: Encoding (örn: 'gzip')
            metadata: Özel metadata dict'i
        
        Returns:
            dict: {success, bucket, key, url}
        
        Örnek:
            # Basit yükleme
            s3.upload_file("data.json", "files/data.json")
            
            # Gzip dosya yükleme
            s3.upload_file(
                "data.json.gz",
                "files/data.json.gz",
                content_type="application/json",
                content_encoding="gzip"
            )
        """
        bucket = bucket or self.bucket
        local_path = Path(local_path)
        
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if content_encoding:
            extra_args["ContentEncoding"] = content_encoding
        if metadata:
            extra_args["Metadata"] = metadata
        
        try:
            if extra_args:
                self.client.upload_file(
                    str(local_path), bucket, s3_key,
                    ExtraArgs=extra_args
                )
            else:
                self.client.upload_file(str(local_path), bucket, s3_key)
            
            return {
                "success": True,
                "bucket": bucket,
                "key": s3_key,
                "url": f"s3://{bucket}/{s3_key}"
            }
        except ClientError as e:
            return {"success": False, "error": str(e)}
    
    def upload_bytes(
        self,
        data: bytes,
        s3_key: str,
        bucket: Optional[str] = None,
        content_type: str = "application/octet-stream"
    ) -> Dict[str, Any]:
        """
        Bytes verisini doğrudan S3'e yükle.
        
        Args:
            data: Yüklenecek bytes verisi
            s3_key: S3'teki key
            bucket: Bucket adı
            content_type: MIME type
        
        Returns:
            dict: {success, bucket, key}
        
        Örnek:
            # JSON string'i doğrudan yükle
            data = json.dumps({"hello": "world"}).encode()
            s3.upload_bytes(data, "data.json", content_type="application/json")
            
            # Gzip'li veri yükle
            compressed = gzip.compress(json.dumps(data).encode())
            s3.upload_bytes(compressed, "data.json.gz")
        """
        bucket = bucket or self.bucket
        
        try:
            self.client.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=data,
                ContentType=content_type
            )
            return {"success": True, "bucket": bucket, "key": s3_key}
        except ClientError as e:
            return {"success": False, "error": str(e)}
    
    def download_file(
        self,
        s3_key: str,
        local_path: Union[str, Path],
        bucket: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        S3'ten dosya indir.
        
        Args:
            s3_key: S3'teki key
            local_path: İndirilecek lokal yol
            bucket: Bucket adı
        
        Returns:
            dict: {success, local_path}
        
        Örnek:
            s3.download_file("files/data.json", "local_data.json")
        """
        bucket = bucket or self.bucket
        local_path = Path(local_path)
        
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            self.client.download_file(bucket, s3_key, str(local_path))
            return {"success": True, "local_path": str(local_path)}
        except ClientError as e:
            return {"success": False, "error": str(e)}
    
    def get_object(
        self,
        s3_key: str,
        bucket: Optional[str] = None,
        decompress_gzip: bool = False
    ) -> Dict[str, Any]:
        """
        S3'ten objeyi oku ve içeriğini döndür.
        
        Args:
            s3_key: S3'teki key
            bucket: Bucket adı
            decompress_gzip: True ise gzip decompress yap
        
        Returns:
            dict: {success, content, content_type, size}
        
        Örnek:
            # JSON dosyası oku
            result = s3.get_object("data.json")
            data = json.loads(result['content'])
            
            # Gzip'li dosya oku
            result = s3.get_object("data.json.gz", decompress_gzip=True)
            data = json.loads(result['content'])
        """
        bucket = bucket or self.bucket
        
        try:
            response = self.client.get_object(Bucket=bucket, Key=s3_key)
            content = response["Body"].read()
            
            if decompress_gzip:
                content = gzip.decompress(content)
            
            return {
                "success": True,
                "content": content.decode("utf-8"),
                "content_type": response.get("ContentType"),
                "size": response.get("ContentLength")
            }
        except ClientError as e:
            return {"success": False, "error": str(e)}
    
    def delete_object(
        self,
        s3_key: str,
        bucket: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        S3'ten obje sil.
        
        Args:
            s3_key: Silinecek objenin key'i
            bucket: Bucket adı
        
        Returns:
            dict: {success, key}
        """
        bucket = bucket or self.bucket
        
        try:
            self.client.delete_object(Bucket=bucket, Key=s3_key)
            return {"success": True, "key": s3_key}
        except ClientError as e:
            return {"success": False, "error": str(e)}
    
    def delete_objects(
        self,
        s3_keys: List[str],
        bucket: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Birden fazla objeyi toplu sil.
        
        Args:
            s3_keys: Silinecek key listesi
            bucket: Bucket adı
        
        Returns:
            dict: {success, deleted_count}
        
        Örnek:
            s3.delete_objects(["file1.txt", "file2.txt", "file3.txt"])
        """
        bucket = bucket or self.bucket
        
        try:
            response = self.client.delete_objects(
                Bucket=bucket,
                Delete={"Objects": [{"Key": key} for key in s3_keys]}
            )
            deleted = len(response.get("Deleted", []))
            return {"success": True, "deleted_count": deleted}
        except ClientError as e:
            return {"success": False, "error": str(e)}
    
    def object_exists(
        self,
        s3_key: str,
        bucket: Optional[str] = None
    ) -> bool:
        """
        Objenin var olup olmadığını kontrol et.
        
        Args:
            s3_key: Kontrol edilecek key
            bucket: Bucket adı
        
        Returns:
            bool: Obje varsa True
        """
        bucket = bucket or self.bucket
        
        try:
            self.client.head_object(Bucket=bucket, Key=s3_key)
            return True
        except ClientError:
            return False
    
    def generate_presigned_url(
        self,
        s3_key: str,
        bucket: Optional[str] = None,
        expiration: int = 3600,
        http_method: str = "GET"
    ) -> str:
        """
        Geçici erişim URL'i oluştur.
        
        Args:
            s3_key: Obje key'i
            bucket: Bucket adı
            expiration: URL geçerlilik süresi (saniye)
            http_method: 'GET' veya 'PUT'
        
        Returns:
            str: Presigned URL
        
        Örnek:
            # 1 saatlik download linki
            url = s3.generate_presigned_url("private/file.pdf")
            
            # 5 dakikalık upload linki
            url = s3.generate_presigned_url(
                "uploads/new.pdf",
                expiration=300,
                http_method="PUT"
            )
        """
        bucket = bucket or self.bucket
        
        client_method = "get_object" if http_method == "GET" else "put_object"
        
        return self.client.generate_presigned_url(
            ClientMethod=client_method,
            Params={"Bucket": bucket, "Key": s3_key},
            ExpiresIn=expiration
        )


# =============================================================================
# BÖLÜM 3: LAMBDA İŞLEMLERİ
# =============================================================================

class LambdaOperations:
    """
    AWS Lambda Fonksiyon İşlemleri
    
    Kullanım:
        config = AWSConfig().load_from_env()
        lam = LambdaOperations(config)
        
        # Fonksiyonları listele
        lam.list_functions()
        
        # Fonksiyon çağır
        lam.invoke("my-function", {"key": "value"})
    """
    
    def __init__(self, config: AWSConfig):
        self.config = config
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            self._client = self.config.get_client('lambda')
        return self._client
    
    def list_functions(self) -> List[Dict[str, Any]]:
        """
        Tüm Lambda fonksiyonlarını listele.
        
        Returns:
            List[dict]: Her fonksiyon için {name, runtime, memory, timeout, last_modified}
        
        Örnek:
            functions = lam.list_functions()
            for f in functions:
                print(f"{f['name']} ({f['runtime']}) - {f['memory']}MB")
        """
        response = self.client.list_functions()
        
        return [
            {
                "name": f["FunctionName"],
                "runtime": f.get("Runtime"),
                "memory": f.get("MemorySize"),
                "timeout": f.get("Timeout"),
                "last_modified": f.get("LastModified"),
                "arn": f.get("FunctionArn")
            }
            for f in response.get("Functions", [])
        ]
    
    def get_function(self, function_name: str) -> Dict[str, Any]:
        """
        Fonksiyon detaylarını getir.
        
        Args:
            function_name: Fonksiyon adı veya ARN
        
        Returns:
            dict: Fonksiyon konfigürasyonu
        """
        try:
            response = self.client.get_function(FunctionName=function_name)
            config = response["Configuration"]
            return {
                "success": True,
                "name": config["FunctionName"],
                "runtime": config.get("Runtime"),
                "handler": config.get("Handler"),
                "memory": config.get("MemorySize"),
                "timeout": config.get("Timeout"),
                "environment": config.get("Environment", {}).get("Variables", {}),
                "arn": config.get("FunctionArn")
            }
        except ClientError as e:
            return {"success": False, "error": str(e)}
    
    def invoke(
        self,
        function_name: str,
        payload: Optional[Dict] = None,
        invocation_type: str = "RequestResponse"
    ) -> Dict[str, Any]:
        """
        Lambda fonksiyonunu çağır.
        
        Args:
            function_name: Fonksiyon adı veya ARN
            payload: Fonksiyona gönderilecek JSON verisi
            invocation_type: 
                - "RequestResponse": Senkron (yanıt bekle)
                - "Event": Asenkron (yanıt bekleme)
                - "DryRun": Sadece izinleri kontrol et
        
        Returns:
            dict: {success, status_code, response, executed_version}
        
        Örnek:
            # Senkron çağrı
            result = lam.invoke("my-function", {"name": "Kaan"})
            if result['success']:
                print(result['response'])
            
            # Asenkron çağrı (fire & forget)
            lam.invoke("my-function", {"data": "..."}, invocation_type="Event")
        """
        try:
            invoke_params = {
                "FunctionName": function_name,
                "InvocationType": invocation_type
            }
            
            if payload:
                invoke_params["Payload"] = json.dumps(payload)
            
            response = self.client.invoke(**invoke_params)
            
            result = {
                "success": True,
                "status_code": response["StatusCode"],
                "executed_version": response.get("ExecutedVersion")
            }
            
            if invocation_type == "RequestResponse":
                payload_response = response["Payload"].read().decode("utf-8")
                try:
                    result["response"] = json.loads(payload_response)
                except json.JSONDecodeError:
                    result["response"] = payload_response
            
            return result
            
        except ClientError as e:
            return {"success": False, "error": str(e)}
    
    def update_function_code(
        self,
        function_name: str,
        zip_file: Optional[Union[str, Path, bytes]] = None,
        s3_bucket: Optional[str] = None,
        s3_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Lambda fonksiyon kodunu güncelle.
        
        Args:
            function_name: Fonksiyon adı
            zip_file: Lokal zip dosyası yolu veya bytes
            s3_bucket: S3'teki zip dosyasının bucket'ı
            s3_key: S3'teki zip dosyasının key'i
        
        Returns:
            dict: {success, version, last_modified}
        
        Örnek:
            # Lokal zip'ten güncelle
            lam.update_function_code("my-function", zip_file="function.zip")
            
            # S3'ten güncelle
            lam.update_function_code(
                "my-function",
                s3_bucket="my-bucket",
                s3_key="deployments/function.zip"
            )
        """
        try:
            params = {"FunctionName": function_name}
            
            if zip_file:
                if isinstance(zip_file, bytes):
                    params["ZipFile"] = zip_file
                else:
                    with open(zip_file, "rb") as f:
                        params["ZipFile"] = f.read()
            elif s3_bucket and s3_key:
                params["S3Bucket"] = s3_bucket
                params["S3Key"] = s3_key
            
            response = self.client.update_function_code(**params)
            
            return {
                "success": True,
                "version": response.get("Version"),
                "last_modified": response.get("LastModified")
            }
        except ClientError as e:
            return {"success": False, "error": str(e)}
    
    def update_environment(
        self,
        function_name: str,
        variables: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Lambda environment variables güncelle.
        
        Args:
            function_name: Fonksiyon adı
            variables: Ortam değişkenleri dict'i
        
        Returns:
            dict: {success, variables}
        
        Örnek:
            lam.update_environment("my-function", {
                "S3_BUCKET": "new-bucket",
                "DEBUG": "true"
            })
        """
        try:
            response = self.client.update_function_configuration(
                FunctionName=function_name,
                Environment={"Variables": variables}
            )
            return {
                "success": True,
                "variables": response.get("Environment", {}).get("Variables", {})
            }
        except ClientError as e:
            return {"success": False, "error": str(e)}


# =============================================================================
# BÖLÜM 4: API GATEWAY İŞLEMLERİ
# =============================================================================

class APIGatewayOperations:
    """
    API Gateway İşlemleri
    
    Not: SAM ile deploy edilen API Gateway'ler için genellikle
    doğrudan boto3 kullanmaya gerek yoktur. SAM template'i
    API Gateway'i otomatik oluşturur.
    
    Bu class daha çok mevcut API'leri listelemek ve
    bilgi almak için kullanılır.
    """
    
    def __init__(self, config: AWSConfig):
        self.config = config
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            self._client = self.config.get_client('apigateway')
        return self._client
    
    def list_apis(self) -> List[Dict[str, Any]]:
        """
        Tüm REST API'leri listele.
        
        Returns:
            List[dict]: Her API için {id, name, created_date}
        """
        response = self.client.get_rest_apis()
        
        return [
            {
                "id": api["id"],
                "name": api["name"],
                "created_date": api.get("createdDate", "").isoformat() if api.get("createdDate") else None
            }
            for api in response.get("items", [])
        ]
    
    def get_api_stages(self, api_id: str) -> List[Dict[str, Any]]:
        """
        API'nin stage'lerini listele.
        
        Args:
            api_id: REST API ID
        
        Returns:
            List[dict]: Stage bilgileri
        """
        response = self.client.get_stages(restApiId=api_id)
        
        return [
            {
                "stage_name": stage["stageName"],
                "deployment_id": stage.get("deploymentId"),
                "created_date": stage.get("createdDate", "").isoformat() if stage.get("createdDate") else None
            }
            for stage in response.get("item", [])
        ]
    
    def get_endpoint_url(self, api_id: str, stage: str = "Prod") -> str:
        """
        API endpoint URL'ini oluştur.
        
        Args:
            api_id: REST API ID
            stage: Stage adı (genellikle "Prod" veya "dev")
        
        Returns:
            str: Endpoint URL
        
        Örnek:
            url = apigw.get_endpoint_url("abc123", "Prod")
            # https://abc123.execute-api.eu-central-1.amazonaws.com/Prod
        """
        region = self.config.region
        return f"https://{api_id}.execute-api.{region}.amazonaws.com/{stage}"


# =============================================================================
# BÖLÜM 5: YARDIMCI FONKSİYONLAR
# =============================================================================

def quick_s3_upload(
    local_path: Union[str, Path],
    s3_key: str,
    bucket: str,
    gzip_compress: bool = False
) -> Dict[str, Any]:
    """
    Hızlı S3 yükleme - tek satırda dosya yükle.
    
    Args:
        local_path: Lokal dosya yolu
        s3_key: S3'teki key
        bucket: Bucket adı
        gzip_compress: True ise gzip sıkıştır
    
    Returns:
        dict: {success, url}
    
    Örnek:
        # Basit yükleme
        quick_s3_upload("data.json", "data.json", "my-bucket")
        
        # Gzip ile yükleme
        quick_s3_upload("large.json", "large.json.gz", "my-bucket", gzip_compress=True)
    """
    config = AWSConfig().load_from_env()
    s3 = S3Operations(config, bucket)
    
    local_path = Path(local_path)
    
    if gzip_compress:
        with open(local_path, "rb") as f:
            compressed = gzip.compress(f.read())
        
        content_type = "application/json" if local_path.suffix == ".json" else "application/octet-stream"
        return s3.upload_bytes(
            compressed, s3_key,
            content_type=content_type
        )
    else:
        return s3.upload_file(local_path, s3_key)


def quick_s3_download(
    s3_key: str,
    bucket: str,
    decompress_gzip: bool = False
) -> str:
    """
    Hızlı S3 okuma - tek satırda dosya içeriği al.
    
    Args:
        s3_key: S3'teki key
        bucket: Bucket adı
        decompress_gzip: True ise gzip decompress yap
    
    Returns:
        str: Dosya içeriği
    
    Örnek:
        content = quick_s3_download("data.json", "my-bucket")
        data = json.loads(content)
    """
    config = AWSConfig().load_from_env()
    s3 = S3Operations(config, bucket)
    
    result = s3.get_object(s3_key, decompress_gzip=decompress_gzip)
    
    if result["success"]:
        return result["content"]
    else:
        raise Exception(result["error"])


def quick_lambda_invoke(function_name: str, payload: Dict = None) -> Any:
    """
    Hızlı Lambda çağrısı - tek satırda fonksiyon çalıştır.
    
    Args:
        function_name: Fonksiyon adı
        payload: Gönderilecek veri
    
    Returns:
        Lambda response
    
    Örnek:
        result = quick_lambda_invoke("my-function", {"name": "Kaan"})
    """
    config = AWSConfig().load_from_env()
    lam = LambdaOperations(config)
    
    result = lam.invoke(function_name, payload)
    
    if result["success"]:
        return result.get("response")
    else:
        raise Exception(result["error"])


# =============================================================================
# ÖRNEK KULLANIM (Test için)
# =============================================================================

if __name__ == "__main__":
    # Konfigürasyon
    config = AWSConfig().load_from_env()
    
    # Bağlantı testi
    print("🔗 AWS Bağlantı Testi...")
    result = config.test_connection()
    
    if result["success"]:
        print(f"✅ Bağlantı başarılı!")
        print(f"   Account: {result['account_id']}")
        print(f"   User: {result['user_arn']}")
    else:
        print(f"❌ Bağlantı hatası: {result['error']}")
