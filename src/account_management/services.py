from uuid import UUID

from entities.user import User

from .account_repository import AbstractAccountRepository


async def pin_memory(
    user: User,
    memory_id: UUID,
    account_repository: AbstractAccountRepository,
):
    """Pin a memory

    Args:
        user (User): The principal invoking the service.
        memory_id (UUID): The memory to pin.
        account_repository (AbstractAccountRepository): A repository of
            accounts.
    """

    account = await account_repository.get_by_user_id(user.id)
    account.pin_memory(memory_id)
    await account_repository.update(account)


async def unpin_memory(
    user: User,
    memory_id: UUID,
    account_repository: AbstractAccountRepository,
):
    """Unpin a memory

    Args:
        user (User): The principal invoking the service.
        memory_id (UUID): The memory to unpin.
        account_repository (AbstractAccountRepository): A repository of
            accounts.
    """
    account = await account_repository.get_by_user_id(user.id)
    account.unpin_memory(memory_id)
    await account_repository.update(account)
