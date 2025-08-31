import logging
from pathlib import Path
from typing import Any

import pytest

from memories.memory_repository import InMemoryMemoryRepository
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
