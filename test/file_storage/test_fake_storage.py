import pytest

from utils.file_storage.exceptions import DataTypeError, FileTooBigError
from utils.file_storage.fake_storage import FakeStorage


class TestFakeFileSys:
    async def test_save(self):
        fake_s3 = FakeStorage("test-bucket")
        await fake_s3.save("test_key", b"test_data")
        assert "test_key" in fake_s3._data  # type: ignore
        assert fake_s3._data["test_key"] == b"test_data"  # type: ignore

    async def test_save_gt_5mb(self):
        fake_s3 = FakeStorage("test-bucket")
        large_data = b"x" * (51 * 1024 * 1024)
        with pytest.raises(FileTooBigError):
            await fake_s3.save("test_key", large_data)

    async def test_save_bad_data_type(self):
        fake_s3 = FakeStorage("test-bucket")
        with pytest.raises(DataTypeError):
            await fake_s3.save("test_key", "some string")  # type: ignore

    async def test_remove(self):
        fake_s3 = FakeStorage("test-bucket")
        await fake_s3.save("test_key", b"test_data")
        assert "test_key" in fake_s3._data  # type: ignore
        await fake_s3.remove("test_key")
        assert "test_key" not in fake_s3._data  # type: ignore
