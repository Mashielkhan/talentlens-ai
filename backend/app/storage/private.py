import re
from functools import lru_cache

from app.core.config import settings


class PrivateStorage:
    def __init__(self):
        self.config = settings()
        if self.config.storage_backend == "s3":
            import boto3

            self.client = boto3.client("s3", endpoint_url=self.config.s3_endpoint_url or None)

    def _path(self, key):
        if not re.fullmatch(r"[0-9a-f-]{36}\.(pdf|docx)", key):
            raise ValueError("Invalid private object key")
        return self.config.storage_path / key

    def put(self, key, data):
        path = self._path(key)
        if self.config.storage_backend == "s3":
            self.client.put_object(
                Bucket=self.config.s3_bucket, Key=key, Body=data, ServerSideEncryption="AES256"
            )
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(data)

    def read(self, key):
        path = self._path(key)
        if self.config.storage_backend == "s3":
            return self.client.get_object(Bucket=self.config.s3_bucket, Key=key)["Body"].read()
        return path.read_bytes()

    def delete(self, key):
        path = self._path(key)
        if self.config.storage_backend == "s3":
            self.client.delete_object(Bucket=self.config.s3_bucket, Key=key)
        else:
            path.unlink(missing_ok=True)


@lru_cache
def storage():
    return PrivateStorage()
