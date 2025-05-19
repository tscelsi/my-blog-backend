import supabase

from utils.file_storage.base_storage import AbstractFileStorage
from utils.file_storage.exceptions import DataTypeError, FileTooBigError


class SupabaseStorage(AbstractFileStorage):
    def __init__(self, bucket: str, client: supabase.AsyncClient):
        self.bucket = bucket
        self.client = client

    async def save(self, key: str, data: bytes):
        # we only allow upload of files < 5MB
        if isinstance(data, bytes):
            if len(data) > (50 * 1024 * 1024):
                raise FileTooBigError("File size exceeds 50MB")
        else:
            raise DataTypeError("Data must be bytes or a file-like object")
        await self.client.storage.from_(self.bucket).upload(
            key, data, {"upsert": "true"}
        )

    async def remove(self, key: str):
        # Implement the logic to remove the file from Supabase bucket here
        await self.client.storage.from_(self.bucket).remove([key])  # type: ignore  # noqa

    async def generate_presigned_url(self, key: str) -> str:
        # Generate a presigned URL for the file in Supabase bucket
        res = await self.client.storage.from_(self.bucket).create_signed_url(
            key,
            60 * 60 * 24,  # 1 day expiration
            {"download": True},
        )
        return res["signedUrl"]
