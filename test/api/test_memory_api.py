from fastapi import FastAPI
from fastapi.testclient import TestClient

from account_management.account_repository import InMemoryAccountRepository
from api.memory_router import (
    get_account_repository_dep,
    get_service_manager_dep,
)
from api.service_manager import ServiceManager
from memories.memory_repository import InMemoryMemoryRepository
from sharing.resource_repository import CedarResourceInMemoryRepository
from sharing.resources import CedarAccount, CedarMemory
from test import fixtures
from utils.file_storage.fake_storage import FakeStorage


async def test_pin_memory(test_app: FastAPI):
    user = fixtures.create_user()
    account = fixtures.create_account_with_user(user)
    memory = fixtures.create_memory_with_user(user)
    account_repo = InMemoryAccountRepository([account])
    memory_repo = InMemoryMemoryRepository([memory])
    sm = ServiceManager(
        memory_repo,
        FakeStorage(bucket="euw2.meapp.t0mm08669.develop"),
        CedarResourceInMemoryRepository(
            memory_resources=[
                CedarMemory(
                    id=memory.id,
                    owner=memory.owner,
                    editors=memory.editors,
                    readers=memory.readers,
                    private=memory.private,
                )
            ],
            account_resources=[
                CedarAccount(id=fixtures.ACCOUNT_ID, owner=fixtures.USER_ID),
            ],
        ),
    )
    await sm.start()
    test_app.dependency_overrides[get_account_repository_dep] = (
        lambda: account_repo
    )
    test_app.dependency_overrides[get_service_manager_dep] = lambda: sm
    client = TestClient(test_app)
    res = client.put(f"/memory/{memory.id}/set-pin", json={"pin": True})
    assert res.status_code == 204
    updated_account = await account_repo.get_by_user_id(user.id)
    assert memory.id in updated_account.memories_pinned
