"""NOTE: currently deprecated in favour of supabase."""

from aiobotocore import session

from utils.file_storage.base_storage import AbstractFileStorage, S3Credentials
from utils.file_storage.exceptions import DataTypeError, FileTooBigError


class S3Storage(AbstractFileStorage):
    def __init__(self, bucket: str):
        self.bucket = bucket
        self.session = session.get_session()
        self.credentials = S3Credentials()  # type: ignore

    async def save(self, key: str, data: bytes):
        # we only allow upload of files < 5MB
        if isinstance(data, bytes):
            if len(data) > (50 * 1024 * 1024):
                raise FileTooBigError("File size exceeds 50MB")
        else:
            raise DataTypeError("Data must be bytes")
        async with self.session.create_client(  # type: ignore
            "s3",
            region_name=self.credentials.AWS_REGION,
            aws_secret_access_key=self.credentials.AWS_SECRET_ACCESS_KEY,
            aws_access_key_id=self.credentials.AWS_ACCESS_KEY_ID,
        ) as client:  # type: ignore
            await client.put_object(  # type: ignore
                Body=data, Bucket=self.bucket, Key=key, ACL="private"
            )

    async def remove(self, key: str):
        async with self.session.create_client(  # type: ignore
            "s3",
            region_name=self.credentials.AWS_REGION,
            aws_secret_access_key=self.credentials.AWS_SECRET_ACCESS_KEY,
            aws_access_key_id=self.credentials.AWS_ACCESS_KEY_ID,
        ) as client:  # type: ignore
            await client.delete_object(Bucket=self.bucket, Key=key)  # type: ignore  # noqa
            await client.delete_object(Bucket=self.bucket, Key=key)  # type: ignore  # noqa

    async def generate_presigned_url(self, key: str) -> str:
        raise NotImplementedError(
            "S3Storage does not support generate_presigned_url method"
        )
