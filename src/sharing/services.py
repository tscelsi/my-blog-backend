import logging
from uuid import UUID

from memories.memory_repository import AbstractMemoryRepository
from sharing.events import PermissionsEvents
from sharing.user_repository import AbstractUserRepository
from utils.events.pubsub import LocalPublisher

logger = logging.getLogger(__name__)


async def add_editor(
    memory_id: UUID,
    user_email: str,
    memory_repo: AbstractMemoryRepository,
    user_repo: AbstractUserRepository,
    pub: LocalPublisher,
):
    """Add a user as an editor to a memory.

    Args:
        memory_id (UUID): The ID of the memory to which the editor is being
            added.
        user_id (UUID): The ID of the user to be added as an editor.
        repo (AbstractMemoryRepository): The repository to interact with
            memory data.

    Raises:
        AuthorisationError: If the user does not have permission to add an
            editor to the memory.
        MemoryNotFoundError: If the memory with the given ID does not exist.
        UserNotFoundError: If the user with the given email does not exist.
    """
    memory = await memory_repo.get(memory_id)
    user_id = await user_repo.get_user_id_by_email(user_email)
    memory.add_editor(user_id)
    # Save the updated memory back to the repository
    await memory_repo.update_editors(memory)
    pub.publish({"topic": PermissionsEvents.EDITORS_ADDED, "memory": memory})


async def add_reader(
    memory_id: UUID,
    user_email: str,
    memory_repo: AbstractMemoryRepository,
    user_repo: AbstractUserRepository,
    pub: LocalPublisher,
):
    """Add a user as a reader to a memory.

    Args:
        principal (User): The user making the request.
        memory_id (UUID): The ID of the memory to which the editor is being
            added.
        user_email (str): The email of the user to be added as an editor.
        memory_repo (AbstractMemoryRepository): The repository to interact with
            memory data.
        user_repo (AbstractUserRepository): The repository to interact with
            user data.

    Raises:
        AuthorisationError: If the user does not have permission to add an
            editor to the memory.
        MemoryNotFoundError: If the memory with the given ID does not exist.
        UserNotFoundError: If the user with the given email does not exist.
    """
    memory = await memory_repo.get(memory_id)
    user_id = await user_repo.get_user_id_by_email(user_email)
    memory.add_reader(user_id)
    # Save the updated memory back to the repository
    await memory_repo.update_readers(memory)
    pub.publish({"topic": PermissionsEvents.READERS_ADDED, "memory": memory})


async def remove_editor(
    memory_id: UUID,
    user_id: UUID,
    memory_repo: AbstractMemoryRepository,
    pub: LocalPublisher,
):
    """Add a user as an editor to a memory.

    Args:
        principal (User): The user making the request.
        memory_id (UUID): The ID of the memory to which the editor is being
            added.
        user_id (UUID): The ID of the user to be added as an editor.
        repo (AbstractMemoryRepository): The repository to interact with
            memory data.

    Raises:
        AuthorisationError: If the user does not have permission to add an
            editor to the memory.
        MemoryNotFoundError: If the memory with the given ID does not exist.
        UserNotFoundError: If the user with the given email does not exist.
    """
    memory = await memory_repo.get(memory_id)
    memory.remove_editor(user_id)
    # Save the updated memory back to the repository
    await memory_repo.update_editors(memory)
    pub.publish({"topic": PermissionsEvents.EDITORS_REMOVED, "memory": memory})


async def remove_reader(
    memory_id: UUID,
    user_id: UUID,
    memory_repo: AbstractMemoryRepository,
    pub: LocalPublisher,
):
    """Remove a user as an reader to a memory.

    Args:
        principal (User): The user making the request.
        memory_id (UUID): The ID of the memory to which the editor is being
            added.
        user_id (UUID): The ID of the user to be added as an editor.
        repo (AbstractMemoryRepository): The repository to interact with
            memory data.

    Raises:
        AuthorisationError: If the user does not have permission to add an
            editor to the memory.
        MemoryNotFoundError: If the memory with the given ID does not exist.
        UserNotFoundError: If the user with the given email does not exist.
    """
    memory = await memory_repo.get(memory_id)
    memory.remove_reader(user_id)
    # Save the updated memory back to the repository
    await memory_repo.update_readers(memory)
    pub.publish({"topic": PermissionsEvents.READERS_REMOVED, "memory": memory})


async def make_memory_public(
    memory_id: UUID,
    memory_repo: AbstractMemoryRepository,
    pub: LocalPublisher,
):
    """Make a memory publicly readable."""
    memory = await memory_repo.authenticated_get(memory_id)
    memory.make_public()
    await memory_repo.update_public_private(memory)
    pub.publish({"topic": PermissionsEvents.MADE_PUBLIC, "memory": memory})


async def make_memory_private(
    memory_id: UUID,
    memory_repo: AbstractMemoryRepository,
    pub: LocalPublisher,
):
    """Make a Memory only readable/editable by those it is shared with
    explicitly."""
    memory = await memory_repo.authenticated_get(memory_id)
    memory.make_private()
    await memory_repo.update_public_private(memory)
    pub.publish({"topic": PermissionsEvents.MADE_PRIVATE, "memory": memory})
