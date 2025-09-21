import asyncio
import logging
from uuid import UUID

from pydantic import BaseModel

from account_management.account_repository import AbstractAccountRepository
from entities.user import User, UserWithEmail
from memories.memory_repository import AbstractMemoryRepository
from sharing.events import PermissionsEvents
from sharing.exceptions import BaseSharingError
from sharing.user_repository import AbstractUserRepository
from utils.events.pubsub import LocalPublisher

logger = logging.getLogger(__name__)


class MemoryPermissionData(BaseModel):
    id: UUID
    owner: UUID
    editors: list[UserWithEmail]
    readers: list[UserWithEmail]
    private: bool


async def get_permissions(
    memory_id: UUID,
    memory_repo: AbstractMemoryRepository,
    user_repo: AbstractUserRepository,
):
    memory = await memory_repo.get(memory_id)
    editor_ids = memory.editors
    reader_ids = memory.readers
    user_ids = editor_ids.union(reader_ids)
    if not user_ids:
        return MemoryPermissionData(
            id=memory.id,
            owner=memory.owner,
            editors=[],
            readers=[],
            private=memory.private,
        )
    # Fetch emails for editors and readers
    res = await user_repo.get_user_emails_by_ids(editor_ids.union(reader_ids))
    editors = [x for x in res if x.id in editor_ids]
    readers = [x for x in res if x.id in reader_ids]
    return MemoryPermissionData(
        id=memory.id,
        owner=memory.owner,
        editors=editors,
        readers=readers,
        private=memory.private,
    )


async def add_editor(
    principal: User,
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
    if user_id == principal.id:
        raise BaseSharingError("Cannot add yourself as an editor")
    memory.add_editor(user_id)
    # Save the updated memory back to the repository
    await memory_repo.update_editors(memory)
    pub.publish({"topic": PermissionsEvents.EDITORS_ADDED, "memory": memory})


async def add_reader(
    principal: User,
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
    if user_id == principal.id:
        raise BaseSharingError("Cannot add yourself as a reader")
    memory.add_reader(user_id)
    # Save the updated memory back to the repository
    await memory_repo.update_readers(memory)
    pub.publish({"topic": PermissionsEvents.READERS_ADDED, "memory": memory})


async def remove_editor(
    memory_id: UUID,
    user_id: UUID,
    memory_repo: AbstractMemoryRepository,
    account_repo: AbstractAccountRepository,
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
    memory, account = await asyncio.gather(
        memory_repo.get(memory_id), account_repo.get_by_user_id(user_id)
    )
    memory.remove_editor(user_id)
    account.unpin_memory(memory_id)
    # Persist the updated memory and account
    await asyncio.gather(
        memory_repo.update_editors(memory), account_repo.update(account)
    )
    pub.publish({"topic": PermissionsEvents.EDITORS_REMOVED, "memory": memory})


async def remove_reader(
    memory_id: UUID,
    user_id: UUID,
    memory_repo: AbstractMemoryRepository,
    account_repo: AbstractAccountRepository,
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
    memory, account = await asyncio.gather(
        memory_repo.get(memory_id), account_repo.get_by_user_id(user_id)
    )
    memory.remove_reader(user_id)
    account.unpin_memory(memory_id)
    # Persist the updated memory and account
    await asyncio.gather(
        memory_repo.update_readers(memory), account_repo.update(account)
    )
    pub.publish({"topic": PermissionsEvents.READERS_REMOVED, "memory": memory})


async def make_memory_public(
    memory_id: UUID,
    memory_repo: AbstractMemoryRepository,
    pub: LocalPublisher,
):
    """Make a memory publicly readable."""
    memory = await memory_repo.get(memory_id)
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
    memory = await memory_repo.get(memory_id)
    memory.make_private()
    await memory_repo.update_public_private(memory)
    pub.publish({"topic": PermissionsEvents.MADE_PRIVATE, "memory": memory})
