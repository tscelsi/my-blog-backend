from uuid import uuid4

import pytest
import supabase

from entities.memory import MemoryAlreadyExistsError
from memories.memory_repository import (
    InMemoryMemoryRepository,
    MemoryNotFoundError,
    SupabaseMemoryRepository,
)
from test import fixtures


@pytest.fixture()
def memory_repo():
    repo = InMemoryMemoryRepository()
    yield repo
    repo._memories.clear()  # type: ignore


class TestInMemoryRepository:
    async def test_create_memory(self, memory_repo: InMemoryMemoryRepository):
        memory = fixtures.create_memory()
        await memory_repo.create_empty(memory=memory)
        with pytest.raises(MemoryAlreadyExistsError):
            await memory_repo.create_empty(memory=memory)
        assert memory_repo.size == 1

    async def test_get_memory(self, memory_repo: InMemoryMemoryRepository):
        memory = fixtures.create_memory()
        await memory_repo.create_empty(memory=memory)
        retrieved_memory = await memory_repo.authenticated_get(memory.id)
        assert memory.id == retrieved_memory.id

    async def test_get_memory_raises_when_not_exists(
        self, memory_repo: InMemoryMemoryRepository
    ):
        with pytest.raises(MemoryNotFoundError):
            await memory_repo.authenticated_get(uuid4())


@pytest.fixture
async def supabase_client():
    from api.service_manager import SupabaseSettings

    settings = SupabaseSettings()  # type: ignore
    async_client = await supabase.create_async_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_KEY,
    )
    return async_client


@pytest.mark.skip(reason="Supabase connected tests are skipped by default")
class TestSupabaseRepository:
    async def test_crud_memory(self, supabase_client: supabase.AsyncClient):
        repo = SupabaseMemoryRepository(supabase_client)
        memory = fixtures.create_memory()
        await repo.create_empty(memory)
        res = await repo.authenticated_get(memory.id)
        assert res.id == memory.id
        assert len(res.fragments) == 1
        with pytest.raises(MemoryAlreadyExistsError):
            await repo.create_empty(memory)
        memory.fragments = []
        await repo.update(memory)
        res = await repo.authenticated_get(memory.id)
        assert len(res.fragments) == 0
        await repo.delete(memory)

    async def test_delete_non_existent_memory(
        self, supabase_client: supabase.AsyncClient
    ):
        repo = SupabaseMemoryRepository(supabase_client)
        memory = fixtures.create_memory()
        await repo.delete(memory)  # noop

    async def test_update_non_existent_memory(
        self, supabase_client: supabase.AsyncClient
    ):
        repo = SupabaseMemoryRepository(supabase_client)
        memory = fixtures.create_memory()
        await repo.update(memory)
