import logging
from typing import BinaryIO
from uuid import UUID

from events.pubsub import LocalPublisher
from fragments.base import FragmentType
from fragments.file import File, FileFragmentFactory
from fragments.text import Op, RichText, Text
from memory import Memory
from memory_repository import AbstractMemoryRepository
from tags import Tag
from utils.background_tasks import BackgroundTasks
from utils.file_storage.base_storage import AbstractFileStorage

logger = logging.getLogger(__name__)


async def create_memory_from_file(
    user_id: UUID,
    memory_title: str,
    type: FragmentType,
    filename: str,
    file: BinaryIO,
    ifilesys: AbstractFileStorage,
    memory_repo: AbstractMemoryRepository,
    background_tasks: BackgroundTasks,
    pub: LocalPublisher,
) -> UUID:
    """Create a Memory from a file.

    Args:
        user_id (UUID): The ID of the user.
        memory_title (str): The title of the Memory.
        filename (str): The name of the file.
        file (BinaryIO): The file to save, opened in binary mode.
        ifilesys (AbstractFileStorage): The file system interface.
        memory_repo (AbstractMemoryRepository): Repository of Memories.
        background_tasks (BackgroundTasks): Background task runner.
        pub (LocalPublisher): Event publisher.

    Returns:
        UUID: The ID of the newly created Memory.
    """
    ff = FileFragmentFactory.create_file_fragment(filename, type=type)
    memory = Memory(title=memory_title, user_id=user_id, fragments=[ff])
    await memory_repo.create(memory)  # commits
    background_tasks.add(save_file, ff, memory, file.read(), ifilesys, pub)
    return memory.id


async def create_memory_from_text(
    user_id: UUID,
    memory_title: str,
    text: str,
    memory_repo: AbstractMemoryRepository,
) -> UUID:
    """Create a Memory from text.

    Args:
        user_id (UUID): The ID of the user.
        memory_title (str): The title of the Memory.
        text (str): The text content of the new fragment.
        memory_repo (AbstractMemoryRepository): Repository of Memories.

    Returns:
        UUID: The ID of the newly created Memory.
    """
    tf = Text.from_content(content=text)
    memory = Memory(title=memory_title, user_id=user_id, fragments=[tf])
    await memory_repo.create(memory)  # commits
    return memory.id


async def create_memory_from_rich_text(
    user_id: UUID,
    memory_title: str,
    content: list[Op],
    memory_repo: AbstractMemoryRepository,
) -> UUID:
    """Create a Memory from a rich text representation.

    Args:
        user_id (UUID): The ID of the user.
        memory_title (str): The title of the Memory.
        content (list[Op]): The list of Delta operations making up the rich
            text content.
        memory_repo (AbstractMemoryRepository): Repository of Memories.

    Returns:
        UUID: The ID of the newly created Memory.
    """
    rtf = RichText.from_content(content=content)
    memory = Memory(title=memory_title, user_id=user_id, fragments=[rtf])
    await memory_repo.create(memory)  # commits
    return memory.id


async def update_memory_title_and_ordering(
    memory_id: UUID,
    title: str,
    fragment_ids: list[UUID],
    memory_repo: AbstractMemoryRepository,
):
    """Update the title and ordering of fragments in a Memory.

    Args:
        memory_id (UUID): The ID of the Memory to update.
        title (str): The new title for the Memory.
        fragment_ids (list[UUID]): The IDs of the fragments in the new order.
        memory_repo (AbstractMemoryRepository): Repository of Memories.
    """
    memory = await memory_repo.get(memory_id)
    memory.title = title
    memory.update_fragment_ordering(fragment_ids)
    await memory_repo.update(memory)
    return memory.id


async def add_file_fragment_to_memory(
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
    memory = await memory_repo.get(memory_id)
    memory.fragments.append(ff)
    await memory_repo.update(memory)
    background_tasks.add(save_file, ff, memory, file.read(), ifilesys, pub)
    return memory.id


async def add_text_fragment_to_memory(
    memory_id: UUID,
    text: str,
    memory_repo: AbstractMemoryRepository,
) -> UUID:
    """Add a text fragment to an existing Memory.

    Args:
        memory_id (UUID): The ID of the Memory to update.
        text (str): The content of the text fragment.
        memory_repo (AbstractMemoryRepository): Repository of Memories.

    Returns:
        UUID: The ID of the updated Memory.
    """
    tf = Text.from_content(content=text)
    memory = await memory_repo.get(memory_id)
    memory.fragments.append(tf)
    await memory_repo.update(memory)
    return memory.id


async def add_rich_text_fragment_to_memory(
    memory_id: UUID,
    content: list[Op],
    memory_repo: AbstractMemoryRepository,
) -> UUID:
    """Add a rich text fragment to an existing Memory.

    Args:
        memory_id (UUID): The ID of the Memory to update.
        content (list[Op]): The content of the rich text fragment.
        memory_repo (AbstractMemoryRepository): Repository of Memories.

    Returns:
        UUID: The ID of the updated Memory.
    """
    rtf = RichText.from_content(content=content)
    memory = await memory_repo.get(memory_id)
    memory.fragments.append(rtf)
    await memory_repo.update(memory)
    return memory.id


async def modify_text_fragment(
    memory_id: UUID,
    fragment_id: UUID,
    text: str,
    memory_repo: AbstractMemoryRepository,
) -> UUID:
    """Modify an existing text fragment.

    Args:
        memory_id (UUID): The ID of the Memory to update.
        fragment_id (UUID): The ID of the text fragment to modify.
        text (str): The content of the text fragment.
        memory_repo (AbstractMemoryRepository): Repository of Memories.

    Returns:
        UUID: The ID of the updated Memory.
    """
    memory = await memory_repo.get(memory_id)
    fragment = memory.get_fragment(fragment_id)
    if not isinstance(fragment, Text):
        raise TypeError(f"Fragment {fragment_id} is not a TextFragment.")
    fragment.content = text
    await memory_repo.update(memory)
    return memory.id


async def modify_rich_text_fragment(
    memory_id: UUID,
    fragment_id: UUID,
    content: list[Op],
    memory_repo: AbstractMemoryRepository,
) -> UUID:
    """Modify an existing rich text fragment.

    Args:
        memory_id (UUID): The ID of the Memory to update.
        fragment_id (UUID): The ID of the rich text fragment to modify.
        text (str): The content of the updated rich text fragment.
        memory_repo (AbstractMemoryRepository): Repository of Memories.

    Returns:
        UUID: The ID of the updated Memory.
    """
    memory = await memory_repo.get(memory_id)
    fragment = memory.get_fragment(fragment_id)
    if not isinstance(fragment, RichText):
        raise TypeError(f"Fragment {fragment_id} is not a RichTextFragment.")
    fragment.content = content
    await memory_repo.update(memory)
    return memory.id


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
        key = fragment.gen_key(memory.user_id)
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
    memory = await repo.get(memory_id)
    fragment = memory.get_fragment(file_fragment_id)
    if not isinstance(fragment, File):
        raise TypeError(f"Fragment {file_fragment_id} is not a FileFragment.")
    fragment.set_upload_succeeded()
    key = fragment.gen_key(memory.user_id)
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
    memory = await repo.get(memory_id)
    fragment = memory.get_fragment(file_fragment_id)
    if not isinstance(fragment, File):
        raise TypeError(f"Fragment {file_fragment_id} is not a FileFragment.")
    fragment.set_upload_progress_error()
    await repo.update(memory)


async def merge_memories(
    memory_a_id: UUID,
    memory_b_id: UUID,
    memory_repo: AbstractMemoryRepository,
):
    """Merge Memory B into Memory A.

    Args:
        memory_a_id (UUID): The ID of the memory to expand.
        memory_b_id (UUID): The ID of the memory being merged.
        memory_repo (AbstractMemoryRepository): Repository of Memories.
    """
    main_memory = await memory_repo.get(memory_a_id)
    merging_memory = await memory_repo.get(memory_b_id)
    main_memory.merge(merging_memory)
    await memory_repo.update(main_memory)
    await memory_repo.delete(merging_memory)


async def split_memory(
    memory_id: UUID,
    fragment_ids: list[UUID],
    memory_repo: AbstractMemoryRepository,
):
    """Split a Memory in two.

    Args:
        memory_id (UUID): The ID of the memory to split.
        fragment_ids (list[UUID]): The IDs of the fragments to split.
        memory_repo (AbstractMemoryRepository): Repository of Memories.
    """
    memory = await memory_repo.get(memory_id)
    old_memory, new_memory = memory.split(fragment_ids)
    await memory_repo.update(old_memory)
    await memory_repo.create(new_memory)


async def forget_fragments(
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
    memory = await memory_repo.get(memory_id)
    file_keys: list[str] = []
    for fragment_id in fragment_ids:
        fragment = memory.get_fragment(fragment_id)
        if isinstance(fragment, File):
            file_keys.append(fragment.gen_key(memory.user_id))
        memory.forget_fragment(fragment_id)
    await memory_repo.update(memory)
    for key in file_keys:
        background_tasks.add(delete_file, key, ifilesys, pub)


async def forget_memory(
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
    memory = await memory_repo.get(memory_id)
    file_keys: list[str] = []
    for fragment in memory.fragments:
        if isinstance(fragment, File):
            file_keys.append(fragment.gen_key(memory.user_id))
    await memory_repo.delete(memory)
    for key in file_keys:
        background_tasks.add(delete_file, key, ifilesys, pub)


async def make_memory_public(
    memory_id: UUID,
    memory_repo: AbstractMemoryRepository,
):
    """Mark a memory as draft."""
    memory = await memory_repo.get(memory_id)
    memory.make_public()
    await memory_repo.update_public_private(memory)


async def make_memory_private(
    memory_id: UUID,
    memory_repo: AbstractMemoryRepository,
):
    """Finalise a memory."""
    memory = await memory_repo.get(memory_id)
    memory.make_private()
    await memory_repo.update_public_private(memory)


async def pin_memory(
    memory_id: UUID,
    memory_repo: AbstractMemoryRepository,
):
    """Pin a memory."""
    memory = await memory_repo.get(memory_id)
    memory.pin()
    await memory_repo.update_pin_status(memory)


async def unpin_memory(
    memory_id: UUID,
    memory_repo: AbstractMemoryRepository,
):
    """Unpin a memory."""
    memory = await memory_repo.get(memory_id)
    memory.unpin()
    await memory_repo.update_pin_status(memory)


async def update_tags(
    memory_id: UUID,
    tags: set[Tag],
    memory_repo: AbstractMemoryRepository,
):
    """Update the tags associated with a memory."""
    memory = await memory_repo.get(memory_id)
    memory.set_tags(tags)
    await memory_repo.update_tags(memory)
