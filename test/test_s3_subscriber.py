import asyncio

from entities.fragments.file import File, FileFragmentStatus
from events.event_defs import StorageEvents
from events.pubsub import LocalPublisher
from events.file_storage_event_handler import FileStorageEventHandler
from memory_repository import InMemoryMemoryRepository
from test import fixtures
from utils.file_storage.fake_storage import FakeStorage


async def test_s3_subscriber_handle_upload_error(
    pub: LocalPublisher, ifilesys: FakeStorage
):
    memory = fixtures.create_memory()
    fragment = memory.fragments[0]
    assert isinstance(fragment, File)
    repo = InMemoryMemoryRepository(memories=[memory])
    filesys_sub = FileStorageEventHandler(pub, repo, ifilesys)
    filesys_sub.subscribe(["filesys_save_error"])
    pub.publish(
        {
            "topic": "filesys_save_error",
            "fragment": fragment,
            "memory": memory,
        }
    )
    await asyncio.sleep(0)
    assert pub._latest_event["topic"] == "filesys_save_error"  # type: ignore
    assert fragment.status == FileFragmentStatus.ERROR
    await filesys_sub.unsubscribe()


async def test_s3_subscriber_handle_upload_success(
    pub: LocalPublisher, ifilesys: FakeStorage
):
    memory = fixtures.create_memory()
    fragment = memory.fragments[0]
    assert isinstance(fragment, File)
    repo = InMemoryMemoryRepository(memories=[memory])
    s3_sub = FileStorageEventHandler(pub, repo, ifilesys)
    s3_sub.subscribe(["filesys_save_success"])
    pub.publish(
        {
            "topic": StorageEvents.FILESYS_SAVE_SUCCESS,
            "fragment": fragment,
            "memory": memory,
        }
    )
    await asyncio.sleep(0)
    assert pub._latest_event["topic"] == StorageEvents.FILESYS_SAVE_SUCCESS  # type: ignore  # noqa
    assert fragment.status == FileFragmentStatus.UPLOADED
    assert fragment.upload_progress == 100
    await s3_sub.unsubscribe()
