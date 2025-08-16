from uuid import UUID

from entities.fragments.base import FragmentType
from entities.fragments.file import File
from entities.memory import Memory
from entities.user import User

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


def create_user():
    return User(id=USER_ID, account=ACCOUNT_ID)
