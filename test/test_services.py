import io

from events.pubsub import LocalPublisher
from fragments.base import FragmentType
from fragments.file import File, FileFragmentStatus
from fragments.text import Text
from memory_repository import InMemoryMemoryRepository
from services import (
    create_memory_from_file,
    create_memory_from_text,
    save_file,
)
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
    memory = await repo.get(memory_id)
    file_fragment = memory.fragments[0]
    assert isinstance(file_fragment, File)
    assert file_fragment.status == FileFragmentStatus.UPLOADING
    assert background_tasks.size == 1
    await background_tasks.join()
    assert pub._latest_event["topic"] == "filesys_save_success"  # type: ignore  # noqa


async def test_create_memory_from_text():
    repo = InMemoryMemoryRepository()
    memory_id = await create_memory_from_text(
        USER_ID, "test memory title", "test text", InMemoryMemoryRepository()
    )
    memory = await repo.get(memory_id)
    text_fragment = memory.fragments[0]
    assert isinstance(text_fragment, Text)
    assert text_fragment.content == "test text"
