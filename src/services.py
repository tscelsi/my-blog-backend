import logging
from typing import BinaryIO
from uuid import UUID

from entities.fragments.base import FragmentType
from entities.fragments.file import File, FileFragmentFactory
from entities.fragments.rss import RSSFeed
from entities.fragments.text import Op, RichText
from entities.memory import Memory
from entities.user import User
from events.pubsub import LocalPublisher
from memory_repository import AbstractMemoryRepository
from tags import Tag
from utils.background_tasks import BackgroundTasks
from utils.file_storage.base_storage import AbstractFileStorage
from utils.permissions.authorise import inline_authorise
from utils.rss_parser import RssItem

logger = logging.getLogger(__name__)


async def create_empty_memory(
    user: User,
    memory_title: str,
    memory_repo: AbstractMemoryRepository,
) -> UUID:
    """Create an empty Memory.

    Args:
        user (User): The authenticated user.
        memory_title (str): The title of the Memory.
        memory_repo (AbstractMemoryRepository): Repository of Memories.

    Returns:
        UUID: The ID of the newly created Memory.
    """
    memory = Memory(title=memory_title, owner=user.id, created_by=user.id)
    await memory_repo.create_empty(memory)
    return memory.id


async def list_memories(
    memory_repo: AbstractMemoryRepository,
):
    """List all Memories for the authenticated user.

    Args:
        memory_repo (AbstractMemoryRepository): Repository of Memories.

    Returns:
        list[Memory]: List of Memories owned by the user.
    """
    result = await memory_repo.authenticated_list_all()
    return result


async def get_memory(
    user: User,
    memory_id: UUID,
    memory_repo: AbstractMemoryRepository,
) -> Memory:
    """Get a Memory by its ID.

    Args:
        user (User): The authenticated user.
        memory_id (UUID): The ID of the Memory to retrieve.
        memory_repo (AbstractMemoryRepository): Repository of Memories.

    Returns:
        Memory: The Memory object.
    """
    memory = await memory_repo.authenticated_get(memory_id)
    inline_authorise(user, 'Action::"GetMemory"', memory)
    return memory


async def update_memory_title(
    user: User,
    memory_id: UUID,
    title: str,
    memory_repo: AbstractMemoryRepository,
):
    """Update the title of a Memory.

    Args:
        user (User): The authenticated user.
        memory_id (UUID): The ID of the Memory to update.
        title (str): The new title for the Memory.
        memory_repo (AbstractMemoryRepository): Repository of Memories.
    """
    memory = await memory_repo.authenticated_get(memory_id)
    inline_authorise(user, 'Action::"UpdateMemoryTitle"', memory)
    memory.title = title
    await memory_repo.update(memory)
    return memory.id


async def update_memory_fragment_ordering(
    user: User,
    memory_id: UUID,
    fragment_ids: list[UUID],
    memory_repo: AbstractMemoryRepository,
):
    """Update the ordering of fragments in a Memory.

    Args:
        user (User): The authenticated user.
        memory_id (UUID): The ID of the Memory to update.
        fragment_ids (list[UUID]): The IDs of the fragments in the new order.
        memory_repo (AbstractMemoryRepository): Repository of Memories.
    """
    memory = await memory_repo.authenticated_get(memory_id)
    inline_authorise(user, 'Action::"UpdateFragmentOrder"', memory)
    memory.update_fragment_ordering(fragment_ids)
    await memory_repo.update(memory)
    return memory.id


async def add_file_fragment_to_memory(
    user: User,
    memory_id: UUID,
    type: FragmentType,
    filename: str,
    file: BinaryIO,
    ifilesys: AbstractFileStorage,
    memory_repo: AbstractMemoryRepository,
    background_tasks: BackgroundTasks,
    pub: LocalPublisher,
) -> UUID:
    """Add a file fragment to an existing Memory.

    Args:
        user (User): The authenticated user.
        memory_id (UUID): The ID of the Memory to update.
        type (FragmentType): The type of the file fragment.
        filename (str): The name of the file.
        file (BinaryIO): The file to save, opened in binary mode.
        ifilesys (AbstractFileStorage): The file system interface.
        memory_repo (AbstractMemoryRepository): Repository of Memories.
        background_tasks (BackgroundTasks): Background task runner.
        pub (LocalPublisher): Event publisher.

    Returns:
        UUID: The ID of the updated Memory.
    """
    ff = FileFragmentFactory.create_file_fragment(filename, type=type)
    memory = await memory_repo.authenticated_get(memory_id)
    inline_authorise(user, 'Action::"CreateFragment"', memory)
    memory.fragments.append(ff)
    await memory_repo.update(memory)
    background_tasks.add(save_file, ff, memory, file.read(), ifilesys, pub)
    return ff.id


async def add_rich_text_fragment_to_memory(
    user: User,
    memory_id: UUID,
    content: list[Op],
    memory_repo: AbstractMemoryRepository,
) -> UUID:
    """Add a rich text fragment to an existing Memory.

    Args:
        user (User): The authenticated user.
        memory_id (UUID): The ID of the Memory to update.
        content (list[Op]): The content of the rich text fragment.
        memory_repo (AbstractMemoryRepository): Repository of Memories.

    Returns:
        UUID: The ID of the updated Memory.
    """
    rtf = RichText.from_content(content=content)
    memory = await memory_repo.authenticated_get(memory_id)
    inline_authorise(user, 'Action::"CreateFragment"', memory)
    memory.fragments.append(rtf)
    await memory_repo.update(memory)
    return rtf.id


async def add_rss_feed_to_memory(
    user: User,
    memory_id: UUID,
    urls: list[str],
    memory_repo: AbstractMemoryRepository,
) -> UUID:
    """Add an RSS feed to an existing Memory.

    Args:
        user (User): The authenticated user.
        memory_id (UUID): The ID of the Memory to update.
        url (str): The url of the RSS feed.
        memory_repo (AbstractMemoryRepository): Repository of Memories.

    Returns:
        UUID: The ID of the updated Memory.
    """
    rssf = RSSFeed(urls=urls)
    memory = await memory_repo.authenticated_get(memory_id)
    inline_authorise(user, 'Action::"CreateFragment"', memory)
    memory.fragments.append(rssf)
    await memory_repo.update(memory)
    return rssf.id


async def get_rss_feed_items(
    user: User,
    memory_id: UUID,
    fragment_id: UUID,
    repo: AbstractMemoryRepository,
) -> list[RssItem]:
    """Parse the RSS feed and return the news items, sorted by publication
    date."""
    memory = await repo.authenticated_get(memory_id)
    inline_authorise(user, 'Action::"GetMemory"', memory)
    fragment = memory.get_fragment(fragment_id)
    if not isinstance(fragment, RSSFeed):
        raise TypeError(f"Fragment {fragment_id} is not an RSSFeed Fragment.")
    items = await fragment.load_aggregated_feed()
    return items


async def modify_rss_feed_fragment(
    user: User,
    memory_id: UUID,
    fragment_id: UUID,
    urls: list[str],
    memory_repo: AbstractMemoryRepository,
    n_items: int | None = None,
) -> UUID:
    """Modify an existing RSS feed fragment.

    Args:
        user (User): The authenticated user.
        memory_id (UUID): The ID of the Memory to update.
        fragment_id (UUID): The ID of the RSS feed fragment to modify.
        urls (list[str]): The new URLs for the RSS feed.
        memory_repo (AbstractMemoryRepository): Repository of Memories.

    Returns:
        UUID: The ID of the updated Memory.
    """
    memory = await memory_repo.authenticated_get(memory_id)
    inline_authorise(user, 'Action::"UpdateFragment"', memory)
    fragment = memory.get_fragment(fragment_id)
    if not isinstance(fragment, RSSFeed):
        raise TypeError(f"Fragment {fragment_id} is not an RSSFeed Fragment.")
    fragment.urls = urls
    if n_items is not None:
        fragment.n_items = n_items
    await memory_repo.update(memory)
    return fragment.id


async def modify_rich_text_fragment(
    user: User,
    memory_id: UUID,
    fragment_id: UUID,
    content: list[Op],
    memory_repo: AbstractMemoryRepository,
) -> UUID:
    """Modify an existing rich text fragment.

    Args:
        user (User): The authenticated user.
        memory_id (UUID): The ID of the Memory to update.
        fragment_id (UUID): The ID of the rich text fragment to modify.
        text (str): The content of the updated rich text fragment.
        memory_repo (AbstractMemoryRepository): Repository of Memories.

    Returns:
        UUID: The ID of the updated Memory.
    """
    memory = await memory_repo.authenticated_get(memory_id)
    inline_authorise(user, 'Action::"UpdateFragment"', memory)
    fragment = memory.get_fragment(fragment_id)
    if not isinstance(fragment, RichText):
        raise TypeError(f"Fragment {fragment_id} is not a RichTextFragment.")
    fragment.content = content
    await memory_repo.update(memory)
    return fragment.id


async def save_file(
    fragment: File,
    memory: Memory,
    data: bytes,
    ifilesys: AbstractFileStorage,
    pub: LocalPublisher,
):
    """Save a file to the file system.

    Args:
        fragment (FileFragment): The file fragment to upload.
        memory (Memory): The Memory object containing the fragment.
        data (bytes): The data to upload.
        ifilesys (AbstractFileStorage): The file system interface.
        pub (LocalPublisher): Event publisher.

    Events:
        `filesys_save_error`: Updates the FileFragment for error.
        `filesys_save_success`: Updates the FileFragment for success.
    """
    try:
        key = fragment.gen_key(memory.owner)
        await ifilesys.save(key, data)
    except Exception as e:
        logger.error(f"Error uploading fragment: {fragment}")
        logger.exception(e)
        pub.publish(
            {
                "topic": "filesys_save_error",
                "fragment": fragment,
                "memory": memory,
            }
        )
    else:
        pub.publish(
            {
                "topic": "filesys_save_success",
                "fragment": fragment,
                "memory": memory,
            }
        )


async def delete_file(
    key: str,
    ifilesys: AbstractFileStorage,
    pub: LocalPublisher,
):
    """Remove a file from the remote file system.

    Args:
        key (str): The key of the file to delete.
        ifilesys (AbstractFileStorage): The file system interface.
        pub (LocalPublisher): Event publisher.

    Events:
        `filesys_delete_error`: Error deleting the file.
        `filesys_delete_success`: Successfully deleted the file.
    """
    try:
        await ifilesys.remove(key)
    except Exception as e:
        logger.error(f"Error deleting file: {key}")
        logger.exception(e)
        pub.publish({"topic": "filesys_delete_error", "key": key})
    else:
        pub.publish({"topic": "filesys_delete_success", "key": key})


async def save_file_fragment_upload_success(
    memory_id: UUID,
    file_fragment_id: UUID,
    repo: AbstractMemoryRepository,
    ifilesys: AbstractFileStorage,
):
    """Modify a file fragment to reflect upload success.

    Args:
        memory (Memory): The Memory object containing the fragment.
        file_fragment_id (UUID): The ID of the file fragment.
        repo (AbstractMemoryRepository): Repository of Memories.
    """
    memory = await repo.authenticated_get(memory_id)
    fragment = memory.get_fragment(file_fragment_id)
    if not isinstance(fragment, File):
        raise TypeError(f"Fragment {file_fragment_id} is not a FileFragment.")
    fragment.set_upload_succeeded()
    key = fragment.gen_key(memory.owner)
    url = await ifilesys.generate_presigned_url(key)
    fragment.url = url
    await repo.update(memory)


async def save_file_fragment_upload_error(
    memory_id: UUID, file_fragment_id: UUID, repo: AbstractMemoryRepository
):
    """Modify a file fragment to reflect upload error.

    Args:
        memory (Memory): The Memory object containing the fragment.
        file_fragment_id (UUID): The ID of the file fragment.
        repo (AbstractMemoryRepository): Repository of Memories.
    """
    memory = await repo.authenticated_get(memory_id)
    fragment = memory.get_fragment(file_fragment_id)
    if not isinstance(fragment, File):
        raise TypeError(f"Fragment {file_fragment_id} is not a FileFragment.")
    fragment.set_upload_progress_error()
    await repo.update(memory)


async def forget_fragments(
    user: User,
    memory_id: UUID,
    fragment_ids: list[UUID],
    ifilesys: AbstractFileStorage,
    memory_repo: AbstractMemoryRepository,
    background_tasks: BackgroundTasks,
    pub: LocalPublisher,
):
    """Forget a fragment of a Memory.

    Args:
        memory_id (UUID): The ID of the memory containing the fragment.
        fragment_ids (list[UUID]): The IDs of the fragments to forget.
        ifilesys (AbstractFileStorage): The file system interface.
        memory_repo (AbstractMemoryRepository): Repository of Memories.
        background_tasks (BackgroundTasks): Background task runner.
        pub (LocalPublisher): Event publisher.
    """
    memory = await memory_repo.authenticated_get(memory_id)
    inline_authorise(user, 'Action::"DeleteFragment"', memory)
    file_keys: list[str] = []
    for fragment_id in fragment_ids:
        fragment = memory.get_fragment(fragment_id)
        if isinstance(fragment, File):
            file_keys.append(fragment.gen_key(memory.owner))
        memory.forget_fragment(fragment_id)
    await memory_repo.update(memory)
    for key in file_keys:
        background_tasks.add(delete_file, key, ifilesys, pub)


async def forget_memory(
    user: User,
    memory_id: UUID,
    ifilesys: AbstractFileStorage,
    memory_repo: AbstractMemoryRepository,
    background_tasks: BackgroundTasks,
    pub: LocalPublisher,
):
    """Forget a Memory.

    Args:
        memory_id (UUID): The ID of the memory to forget.
        ifilesys (AbstractFileStorage): The file system interface.
        memory_repo (AbstractMemoryRepository): Repository of Memories.
        background_tasks (BackgroundTasks): Background task runner.
        pub (LocalPublisher): Event publisher.
    """
    memory = await memory_repo.authenticated_get(memory_id)
    inline_authorise(user, 'Action::"DeleteMemory"', memory)
    file_keys: list[str] = []
    for fragment in memory.fragments:
        if isinstance(fragment, File):
            file_keys.append(fragment.gen_key(memory.owner))
    await memory_repo.delete(memory)
    for key in file_keys:
        background_tasks.add(delete_file, key, ifilesys, pub)


async def make_memory_public(
    memory_id: UUID,
    memory_repo: AbstractMemoryRepository,
):
    """Mark a memory as draft."""
    memory = await memory_repo.authenticated_get(memory_id)
    memory.make_public()
    await memory_repo.update_public_private(memory)


async def make_memory_private(
    memory_id: UUID,
    memory_repo: AbstractMemoryRepository,
):
    """Finalise a memory."""
    memory = await memory_repo.authenticated_get(memory_id)
    memory.make_private()
    await memory_repo.update_public_private(memory)


async def pin_memory(
    user: User,
    memory_id: UUID,
    memory_repo: AbstractMemoryRepository,
):
    """Pin a memory."""
    memory = await memory_repo.authenticated_get(memory_id)
    inline_authorise(user, 'Action::"EditPin"', memory)
    memory.pin()
    await memory_repo.update_pin_status(memory)


async def unpin_memory(
    user: User,
    memory_id: UUID,
    memory_repo: AbstractMemoryRepository,
):
    """Unpin a memory."""
    memory = await memory_repo.authenticated_get(memory_id)
    inline_authorise(user, 'Action::"EditPin"', memory)
    memory.unpin()
    await memory_repo.update_pin_status(memory)


async def update_tags(
    user: User,
    memory_id: UUID,
    tags: set[Tag],
    memory_repo: AbstractMemoryRepository,
):
    """Update the tags associated with a memory."""
    memory = await memory_repo.authenticated_get(memory_id)
    inline_authorise(user, 'Action::"EditTags"', memory)
    memory.set_tags(tags)
    await memory_repo.update_tags(memory)
    await memory_repo.update_tags(memory)
