import io

from events.pubsub import LocalPublisher
from fragments.base import FragmentType
from fragments.file import File, FileFragmentStatus
from memory_repository import InMemoryMemoryRepository
from services import (
    create_memory_from_file,
    create_memory_from_rich_text,
    make_memory_private,
    make_memory_public,
    pin_memory,
    save_file,
    unpin_memory,
    update_tags,
)
from tags import Tag
from utils.background_tasks import BackgroundTasks
from utils.file_storage.fake_storage import FakeStorage

from .fixtures import USER_ID, create_memory


class FakeFile(io.BytesIO):
    name: str = "test file"


async def test_save_file(ifilesys: FakeStorage, pub: LocalPublisher):
    m = create_memory()
    file_fragment = m.fragments[0]
    assert isinstance(file_fragment, File)
    await save_file(file_fragment, m, b"x0", ifilesys, pub)
    assert pub._latest_event["topic"] == "filesys_save_success"  # type: ignore  # noqa


async def test_save_file_error(ifilesys: FakeStorage, pub: LocalPublisher):
    m = create_memory()
    file_fragment = m.fragments[0]
    assert isinstance(file_fragment, File)
    await save_file(
        file_fragment,
        m,
        "x0",  # type: ignore
        ifilesys,
        pub,
    )  # data is not bytes, so will error
    assert pub._latest_event["topic"] == "filesys_save_error"  # type: ignore


async def test_save_file_as_memory(ifilesys: FakeStorage, pub: LocalPublisher):
    repo = InMemoryMemoryRepository()
    background_tasks = BackgroundTasks()
    file_data = io.BytesIO(b"x0")
    file_name = "test file"
    memory_id = await create_memory_from_file(
        USER_ID,
        "test memory title",
        FragmentType.FILE,
        file_name,
        file_data,
        ifilesys,
        repo,
        background_tasks,
        pub,
    )
    memory = await repo.authenticated_get(memory_id)
    file_fragment = memory.fragments[0]
    assert isinstance(file_fragment, File)
    assert file_fragment.status == FileFragmentStatus.UPLOADING
    assert background_tasks.size == 1
    await background_tasks.join()
    assert pub._latest_event["topic"] == "filesys_save_success"  # type: ignore  # noqa


async def test_finalise_memory():
    repo = InMemoryMemoryRepository()
    memory_id = await create_memory_from_rich_text(
        USER_ID, "test memory title", [], InMemoryMemoryRepository()
    )
    await make_memory_public(memory_id, repo)
    memory = await repo.authenticated_get(memory_id)
    old_updated_at = memory.updated_at
    assert memory.private is False

    await make_memory_private(memory_id, repo)
    memory = await repo.authenticated_get(memory_id)
    new_updated_at = memory.updated_at
    assert memory.private is True
    assert new_updated_at > old_updated_at, (
        "Updated at should change when marking as draft"
    )


async def test_pin_memory():
    repo = InMemoryMemoryRepository()
    memory_id = await create_memory_from_rich_text(
        USER_ID, "test memory title", [], InMemoryMemoryRepository()
    )
    memory = await repo.authenticated_get(memory_id)
    assert memory.pinned is False

    await pin_memory(memory_id, repo)
    memory = await repo.authenticated_get(memory_id)
    old_updated_at = memory.updated_at
    assert memory.pinned is True

    await unpin_memory(memory_id, repo)
    memory = await repo.authenticated_get(memory_id)
    new_updated_at = memory.updated_at
    assert memory.pinned is False
    assert new_updated_at > old_updated_at, (
        "Updated at should change when pinning/unpinning"
    )


async def test_set_tags():
    repo = InMemoryMemoryRepository()
    memory_id = await create_memory_from_rich_text(
        USER_ID, "test memory title", [], InMemoryMemoryRepository()
    )
    tags = {Tag.music, Tag.software}
    await update_tags(memory_id, tags, repo)

    updated_memory = await repo.authenticated_get(memory_id)
    assert updated_memory.tags == tags
