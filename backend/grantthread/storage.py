"""Private immutable object bytes. Never accept filesystem/object keys from callers."""
import os
from pathlib import Path

from .errors import DomainError


class LocalStorage:
    def __init__(self, root=None):
        self.root = Path(root or os.getenv("GRANTTHREAD_DATA_DIR", ".data")).resolve() / "objects"
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, key):
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise DomainError("Invalid object key")
        return path

    def put(self, key, data, content_type="application/octet-stream"):
        path = self.path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def get(self, key):
        try:
            return self.path(key).read_bytes()
        except FileNotFoundError as exc:
            raise DomainError("Source object was not found", "not_found", 404) from exc

    def presign_put(self, key, content_type):
        return None

    def presign_get(self, key, content_type, name):
        return None


class S3Storage:
    def __init__(self):
        import boto3
        self.client = boto3.client("s3")
        self.bucket = os.environ["GRANTTHREAD_BUCKET"]

    def put(self, key, data, content_type="application/octet-stream"):
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)

    def get(self, key):
        # Check before downloading so rejected oversized presigned uploads cannot exhaust Lambda.
        metadata = self.client.head_object(Bucket=self.bucket, Key=key)
        if metadata["ContentLength"] > 5 * 1024 * 1024:
            raise DomainError("Document exceeds the 5 MB limit", "too_large", 413)
        return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()

    def presign_put(self, key, content_type):
        return self.client.generate_presigned_url("put_object", Params={
            "Bucket": self.bucket, "Key": key, "ContentType": content_type,
        }, ExpiresIn=300)

    def presign_get(self, key, content_type, name):
        from urllib.parse import quote
        return self.client.generate_presigned_url("get_object", Params={
            "Bucket": self.bucket, "Key": key, "ResponseContentType": content_type,
            "ResponseContentDisposition": "attachment; filename*=UTF-8''" + quote(name, safe=""),
        }, ExpiresIn=300)


def get_storage():
    return S3Storage() if os.getenv("GRANTTHREAD_MODE") == "aws" else LocalStorage()
