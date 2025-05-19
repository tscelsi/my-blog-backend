import pytest

from utils.file_storage.s3_storage import S3Storage

TEST_BUCKET_NAME = "test-me-t0mm08669-bucket"


@pytest.mark.skip(reason="Real S3 tests should only be run manually")
class TestS3Storage:
    async def test_save(self):
        is3 = S3Storage(TEST_BUCKET_NAME)
        file = b"test_data"
        await is3.save("tscelsi/test_key", file)

    async def test_remove(self):
        is3 = S3Storage(TEST_BUCKET_NAME)
        file = b"test_data"
        await is3.save("tscelsi/test_key", file)
        await is3.remove("test_key")
