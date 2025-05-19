from uuid import UUID

from fragments.base import FragmentType
from fragments.file import File
from memory import Memory

MEMORY_ID = UUID("12345678-1234-5678-1234-567812345678")
FRAGMENT_ID = UUID("12345678-1234-5678-1234-567812345679")
USER_ID = UUID("12345678-1234-5678-1234-567812345678")


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
        user_id=USER_ID,
        title="A Test Memory",
        fragments=[create_file_fragment(name=fragment_name)],
    )
