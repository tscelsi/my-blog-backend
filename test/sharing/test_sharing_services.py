from uuid import uuid4

from account_management.account_repository import InMemoryAccountRepository
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
        fixtures.create_user(),
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
        fixtures.create_user(),
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
    user = fixtures.create_user()
    user_acc = fixtures.create_account_with_user(user)
    editor = fixtures.create_user(id=uuid4(), account_id=uuid4())
    editor_acc = fixtures.create_account_with_user(editor)
    memory = fixtures.create_memory_with_user(user)
    memory.add_editor(editor.id)
    editor_acc.pin_memory(memory.id)
    memory_repo = InMemoryMemoryRepository([memory])
    account_repo = InMemoryAccountRepository([user_acc, editor_acc])

    await remove_editor(
        memory_id=fixtures.MEMORY_ID,
        user_id=editor.id,
        memory_repo=memory_repo,
        account_repo=account_repo,
        pub=pub,
    )

    updated = await account_repo.get_by_user_id(editor.id)
    assert editor.id not in updated.memories_pinned
    topic = pub._latest_event["topic"]  # type: ignore  # noqa
    assert topic == PermissionsEvents.EDITORS_REMOVED


async def test_remove_reader_publishes(pub: LocalPublisher):
    user = fixtures.create_user()
    user_acc = fixtures.create_account_with_user(user)
    reader = fixtures.create_user(id=uuid4(), account_id=uuid4())
    reader_acc = fixtures.create_account_with_user(reader)
    memory = fixtures.create_memory_with_user(user)
    memory.add_reader(reader.id)
    reader_acc.pin_memory(memory.id)
    memory_repo = InMemoryMemoryRepository([memory])
    account_repo = InMemoryAccountRepository([user_acc, reader_acc])

    await remove_reader(
        memory_id=fixtures.MEMORY_ID,
        user_id=reader.id,
        memory_repo=memory_repo,
        account_repo=account_repo,
        pub=pub,
    )

    updated = await account_repo.get_by_user_id(reader.id)
    assert reader.id not in updated.memories_pinned
    topic = pub._latest_event["topic"]  # type: ignore  # noqa
    assert topic == PermissionsEvents.READERS_REMOVED
