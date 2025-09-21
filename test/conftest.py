import logging
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    BaseUser,
)
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import HTTPConnection

from api.memory_router import router as memory_router
from entities.user import User
from memories.memory_repository import InMemoryMemoryRepository
from test.fixtures import ACCOUNT_ID, USER_ID
from utils.events.pubsub import LocalPublisher, LocalSubscriber
from utils.file_storage.fake_storage import FakeStorage

logger = logging.getLogger(__name__)
TEST_DIR = Path(__file__).parent


@pytest.fixture
def memory_repo() -> InMemoryMemoryRepository:
    return InMemoryMemoryRepository()


@pytest.fixture
def ifilesys() -> FakeStorage:
    fake_filesys = FakeStorage("test-bucket")
    return fake_filesys


@pytest.fixture
async def pub():
    pub = LocalPublisher()
    return pub


@pytest.fixture
async def sub(pub: LocalPublisher):
    class SimpleSubscriber(LocalSubscriber):
        async def handle(self, event: dict[str, Any]):
            logger.debug(f"handled: {event}")

    sub = SimpleSubscriber(pub)
    sub.subscribe(
        [
            "filesys_save_error",
            "filesys_save_success",
            "filesys_delete_error",
            "filesys_delete_success",
        ]
    )
    yield sub
    await sub.unsubscribe([])


@pytest.fixture
def rss_content():
    with open(TEST_DIR / "rss.xml", "r") as file:
        return file.read()


@pytest.fixture
def test_app():
    class FakeAuthBackend(AuthenticationBackend):
        async def authenticate(
            self, conn: HTTPConnection
        ) -> tuple[AuthCredentials, BaseUser] | None:
            return AuthCredentials(["authenticated"]), User(
                id=USER_ID, account=ACCOUNT_ID
            )

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["authorization"],
    )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],
    )
    app.add_middleware(
        AuthenticationMiddleware,
        backend=FakeAuthBackend(),
    )

    app.include_router(memory_router, tags=["memory_router"])
    yield app
