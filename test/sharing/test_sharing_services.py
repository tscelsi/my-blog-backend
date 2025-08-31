from uuid import uuid4

from memories.memory_repository import InMemoryMemoryRepository
from sharing.events import PermissionsEvents
from sharing.services import (
    add_editor,
    add_reader,
    remove_editor,
    remove_reader,
)
from sharing.user_repository import InMemoryUserRepository
from test import fixtures
from utils.events.pubsub import LocalPublisher


async def test_add_editor_publishes(pub: LocalPublisher):
    # given a memory owned by the principal
    memory = fixtures.create_memory()
    repo = InMemoryMemoryRepository([memory])

    # and a user repo that can resolve the editor email
    editor_id = uuid4()
    user_repo = InMemoryUserRepository({"editor@example.com": editor_id})

    # when
    await add_editor(
        memory_id=fixtures.MEMORY_ID,
        user_email="editor@example.com",
        memory_repo=repo,
        user_repo=user_repo,
        pub=pub,
    )

    # then
    updated = await repo.get(fixtures.MEMORY_ID)
    assert editor_id in updated.editors
    topic = pub._latest_event["topic"]  # type: ignore  # noqa
    assert topic == PermissionsEvents.EDITORS_ADDED


async def test_add_reader_publishes(pub: LocalPublisher):
    memory = fixtures.create_memory()
    repo = InMemoryMemoryRepository([memory])

    reader_id = uuid4()
    user_repo = InMemoryUserRepository({"reader@example.com": reader_id})

    await add_reader(
        memory_id=fixtures.MEMORY_ID,
        user_email="reader@example.com",
        memory_repo=repo,
        user_repo=user_repo,
        pub=pub,
    )

    updated = await repo.get(fixtures.MEMORY_ID)
    assert reader_id in updated.readers
    topic = pub._latest_event["topic"]  # type: ignore  # noqa
    assert topic == PermissionsEvents.READERS_ADDED


async def test_remove_editor_publishes(pub: LocalPublisher):
    editor_id = uuid4()
    memory = fixtures.create_memory()
    memory.add_editor(editor_id)
    repo = InMemoryMemoryRepository([memory])

    await remove_editor(
        memory_id=fixtures.MEMORY_ID,
        user_id=editor_id,
        memory_repo=repo,
        pub=pub,
    )

    updated = await repo.get(fixtures.MEMORY_ID)
    assert editor_id not in updated.editors
    topic = pub._latest_event["topic"]  # type: ignore  # noqa
    assert topic == PermissionsEvents.EDITORS_REMOVED


async def test_remove_reader_publishes(pub: LocalPublisher):
    reader_id = uuid4()
    memory = fixtures.create_memory()
    memory.add_reader(reader_id)
    repo = InMemoryMemoryRepository([memory])

    await remove_reader(
        memory_id=fixtures.MEMORY_ID,
        user_id=reader_id,
        memory_repo=repo,
        pub=pub,
    )

    updated = await repo.get(fixtures.MEMORY_ID)
    assert reader_id not in updated.readers
    topic = pub._latest_event["topic"]  # type: ignore  # noqa
    assert topic == PermissionsEvents.READERS_REMOVED
