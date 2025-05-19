import pytest
import supabase

from api.service_manager import SupabaseSettings
from utils.file_storage.supabase_storage import SupabaseStorage

TEST_BUCKET_NAME = "test-me-t0mm08669-bucket"


@pytest.fixture
async def supabase_client():
    settings = SupabaseSettings()  # type: ignore
    async_client = await supabase.create_async_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_KEY,
    )
    return async_client


@pytest.mark.skip(reason="Real supabase tests should only be run manually")
class TestSupabaseStorage:
    async def test_save(self, supabase_client: supabase.AsyncClient):
        storage = SupabaseStorage(TEST_BUCKET_NAME, supabase_client)
        await storage.save("tom/test_key", b"test_data")

    async def test_remove(self, supabase_client: supabase.AsyncClient):
        storage = SupabaseStorage(TEST_BUCKET_NAME, supabase_client)
        await storage.remove("tom/test_key")
