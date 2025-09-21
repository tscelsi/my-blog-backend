from uuid import UUID

from entities.fragments.base import FragmentType
from entities.fragments.file import File
from entities.memory import Memory
from entities.user import Account, User

MEMORY_ID = UUID("12345678-1234-5678-1234-567812345678")
FRAGMENT_ID = UUID("12345678-1234-5678-1234-567812345679")
USER_ID = UUID("12345678-1234-5678-1234-567812345678")
ACCOUNT_ID = UUID("12345678-1234-5678-1234-567812345677")


def create_file_fragment(
    id: UUID = FRAGMENT_ID, name: str = "A Test File"
) -> File:
    return File(id=id, name=name, type=FragmentType.FILE)


def create_text_fragment(
    id: UUID = FRAGMENT_ID, content: str = "A Test Text"
) -> File:
    return File(id=id, name=content, type=FragmentType.TEXT)


def create_memory(fragment_name: str = "A Test File") -> Memory:
    return Memory(
        id=MEMORY_ID,
        owner=USER_ID,
        title="A Test Memory",
        fragments=[create_file_fragment(name=fragment_name)],
        created_by=USER_ID,
    )


def create_memory_with_user(user: User) -> Memory:
    return Memory(
        id=MEMORY_ID,
        owner=user.id,
        title="A Test Memory",
        fragments=[create_file_fragment()],
        created_by=user.id,
    )


def create_user(id: UUID = USER_ID, account_id: UUID = ACCOUNT_ID) -> User:
    return User(id=id, account=account_id)


def create_account_with_user(user: User) -> Account:
    return Account(id=ACCOUNT_ID, owner=user.id, memories_pinned=set())
