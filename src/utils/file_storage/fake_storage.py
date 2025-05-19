from utils.file_storage.base_storage import AbstractFileStorage
from utils.file_storage.exceptions import DataTypeError, FileTooBigError


class FakeStorage(AbstractFileStorage):
    def __init__(self, bucket: str, region: str = "eu-west-1"):
        self.bucket = bucket
        self.region = region
        self._data: dict[str, bytes] = {}

    def exists(self, key: str):
        return key in self._data.keys()

    async def save(self, key: str, data: bytes):
        # we only allow upload of files < 5MB
        if isinstance(data, bytes):
            if len(data) > (50 * 1024 * 1024):
                raise FileTooBigError("File size exceeds 50MB")
        else:
            raise DataTypeError("Data must be bytes or a file-like object")
        self._data[key] = data

    async def remove(self, key: str):
        if key not in self._data:
            raise ValueError(f"Key {key} not found")
        del self._data[key]

    async def generate_presigned_url(self, key: str) -> str:
        return f"http://localhost:5000/{self.bucket}/{key}"
