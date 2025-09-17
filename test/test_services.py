from datetime import datetime, timezone
from io import BytesIO

import pytest
from pytest_httpx import HTTPXMock

from entities.fragments.base import FragmentType
from entities.fragments.file import File
from entities.fragments.rss import ListRssFeedError, RSSFeed
from entities.user import User
from memories.memory_repository import InMemoryMemoryRepository
from memories.services import (
    add_file_fragment_to_memory,
    add_rss_feed_to_memory,
    create_empty_memory,
    get_memory,
    pin_memory,
    save_file,
    unpin_memory,
    update_tags,
)
from sharing.services import make_memory_private, make_memory_public
from tags import Tag
from test import fixtures
from utils.background_tasks import BackgroundTasks
from utils.events.pubsub import LocalPublisher
from utils.file_storage.fake_storage import FakeStorage


@pytest.fixture
def user():
    return fixtures.create_user()


async def test_save_file(ifilesys: FakeStorage, pub: LocalPublisher):
    m = fixtures.create_memory()
    file_fragment = m.fragments[0]
    assert isinstance(file_fragment, File)
    await save_file(file_fragment, m, b"x0", ifilesys, pub)
    assert pub._latest_event["topic"] == "filesys_save_success"  # type: ignore  # noqa


async def test_save_file_error(ifilesys: FakeStorage, pub: LocalPublisher):
    m = fixtures.create_memory()
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


async def test_finalise_memory(user: User, pub: LocalPublisher):
    repo = InMemoryMemoryRepository([])
    memory_id = await create_empty_memory(user, "test memory title", repo, pub)
    await make_memory_public(memory_id, repo, pub)
    memory = await repo.get(memory_id)
    old_updated_at = memory.updated_at
    assert memory.private is False

    await make_memory_private(memory_id, repo, pub)
    memory = await repo.get(memory_id)
    new_updated_at = memory.updated_at
    assert memory.private is True
    assert new_updated_at > old_updated_at, (
        "Updated at should change when marking as draft"
    )


async def test_pin_memory(user: User, pub: LocalPublisher):
    repo = InMemoryMemoryRepository([])
    memory_id = await create_empty_memory(user, "test memory title", repo, pub)
    memory = await repo.get(memory_id)
    assert memory.pinned is False

    await pin_memory(memory_id, repo)
    memory = await repo.get(memory_id)
    old_updated_at = memory.updated_at
    assert memory.pinned is True

    await unpin_memory(memory_id, repo)
    memory = await repo.get(memory_id)
    new_updated_at = memory.updated_at
    assert memory.pinned is False
    assert new_updated_at > old_updated_at, (
        "Updated at should change when pinning/unpinning"
    )


async def test_set_tags(user: User, pub: LocalPublisher):
    repo = InMemoryMemoryRepository([])
    memory_id = await create_empty_memory(user, "test memory title", repo, pub)
    tags = {Tag.music, Tag.software}
    await update_tags(memory_id, tags, repo)

    updated_memory = await repo.get(memory_id)
    assert updated_memory.tags == tags


async def test_get_rss_feed_channel_bad_req(
    user: User, httpx_mock: HTTPXMock, pub: LocalPublisher
):
    httpx_mock.add_response(status_code=404)
    repo = InMemoryMemoryRepository([])
    memory_id = await create_empty_memory(user, "rsstest", repo, pub)
    fragment_id = await add_rss_feed_to_memory(
        memory_id, ["https://example.com/rss"], repo
    )
    memory = await repo.get(memory_id)
    fragment = memory.get_fragment(fragment_id)
    assert isinstance(fragment, RSSFeed)
    with pytest.raises(ListRssFeedError):
        await fragment.load_aggregated_feed()


async def test_get_rss_feed_channel(
    user: User, httpx_mock: HTTPXMock, rss_content: str, pub: LocalPublisher
):
    httpx_mock.add_response(status_code=200, text=rss_content)
    repo = InMemoryMemoryRepository([])
    memory_id = await create_empty_memory(user, "rsstest", repo, pub)
    fragment_id = await add_rss_feed_to_memory(
        memory_id, ["https://example.com/rss"], repo
    )
    memory = await repo.get(memory_id)
    fragment = memory.get_fragment(fragment_id)
    assert isinstance(fragment, RSSFeed)
    feed = await fragment.load_aggregated_feed()
    assert len(feed) == 10


async def test_create_memory_creates_permissions(
    user: User, pub: LocalPublisher
):
    repo = InMemoryMemoryRepository([])
    memory_id = await create_empty_memory(user, "test", repo, pub)
    assert memory_id is not None
    memory = await repo.get(memory_id)
    assert memory is not None
    assert memory.owner == user.id
    assert memory.readers == set()


async def test_get_memory_when_no_file_fragments(
    user: User, pub: LocalPublisher, ifilesys: FakeStorage
):
    repo = InMemoryMemoryRepository([])
    memory_id = await create_empty_memory(user, "test", repo, pub)
    memory = await get_memory(memory_id, repo, ifilesys)
    assert memory is not None
    assert memory.owner == user.id
    assert memory.readers == set()
    assert len(memory.fragments) == 0


async def test_get_memory_when_file_fragments(
    user: User, pub: LocalPublisher, ifilesys: FakeStorage
):
    repo = InMemoryMemoryRepository([])
    memory_id = await create_empty_memory(user, "test", repo, pub)
    await add_file_fragment_to_memory(
        memory_id,
        FragmentType.FILE,
        "file.txt",
        BytesIO(b"file contents"),
        ifilesys,
        repo,
        BackgroundTasks(),
        pub,
    )
    # we only use presigned URLs for public memories
    await make_memory_public(memory_id, repo, pub)
    memory = await get_memory(memory_id, repo, ifilesys)
    assert memory is not None
    assert memory.owner == user.id
    assert memory.readers == set()
    assert len(memory.fragments) == 1
    assert isinstance(memory.fragments[0], File)
    assert memory.fragments[0].url is not None


async def test_get_memory_when_file_fragment_url_expired(
    user: User, pub: LocalPublisher, ifilesys: FakeStorage
):
    repo = InMemoryMemoryRepository([])
    memory_id = await create_empty_memory(user, "test", repo, pub)
    await add_file_fragment_to_memory(
        memory_id,
        FragmentType.FILE,
        "file.txt",
        BytesIO(b"file contents"),
        ifilesys,
        repo,
        BackgroundTasks(),
        pub,
    )
    await make_memory_public(memory_id, repo, pub)
    # Manually expire the URL
    expired_date = datetime.now(tz=timezone.utc).replace(year=2000)
    repo._memories[0].fragments[0].url_last_generated = expired_date  # type: ignore  # noqa
    memory = await get_memory(memory_id, repo, ifilesys)
    assert memory is not None
    assert memory.owner == user.id
    assert memory.readers == set()
    assert len(memory.fragments) == 1
    assert isinstance(memory.fragments[0], File)
    assert memory.fragments[0].url is not None
    assert memory.fragments[0].url_last_generated is not None
    assert memory.fragments[0].url_last_generated > expired_date
