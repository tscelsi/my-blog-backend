import abc
import logging
from datetime import datetime, timezone
from uuid import UUID

from supabase import AsyncClient, PostgrestAPIError

from entities.memory import (
    Memory,
    MemoryAlreadyExistsError,
    MemoryNotFoundError,
)
from entities.user import User

logger = logging.getLogger(__name__)


class AbstractMemoryRepository(abc.ABC):
    @abc.abstractmethod
    async def create_empty(self, memory: Memory) -> None:
        pass

    @abc.abstractmethod
    async def get(self, id: UUID) -> Memory:
        pass

    @abc.abstractmethod
    async def public_get(self, id: UUID) -> Memory:
        pass

    @abc.abstractmethod
    async def authenticated_get(self, id: UUID) -> Memory:
        pass

    @abc.abstractmethod
    async def delete(self, memory: Memory) -> None:
        """Delete a memory."""
        pass

    @abc.abstractmethod
    async def list_all(self, user: User) -> list[Memory]:
        pass

    @abc.abstractmethod
    async def public_list_all(self) -> list[Memory]:
        """List all memories."""
        pass

    @abc.abstractmethod
    async def authenticated_list_all(self) -> list[Memory]:
        """List all memories."""
        pass

    @abc.abstractmethod
    async def update(self, memory: Memory) -> None:
        pass

    @abc.abstractmethod
    async def update_public_private(self, memory: Memory) -> None:
        """Mark the memory as a private or public."""
        pass

    @abc.abstractmethod
    async def update_pin_status(self, memory: Memory) -> None:
        """Pin or unpin the memory."""
        pass

    @abc.abstractmethod
    async def update_tags(self, memory: Memory) -> None:
        """Update the tags of the memory."""
        pass

    @abc.abstractmethod
    async def update_readers(self, memory: Memory) -> None:
        """Update the readers of the memory."""
        pass

    @abc.abstractmethod
    async def update_editors(self, memory: Memory) -> None:
        """Update the editors of the memory."""
        pass


class InMemoryMemoryRepository(AbstractMemoryRepository):
    def __init__(self, memories: list[Memory] = []):
        self._memories = memories

    @property
    def size(self):
        return len(self._memories)

    async def create_empty(self, memory: Memory) -> None:
        if memory.id in [m.id for m in self._memories]:
            raise MemoryAlreadyExistsError(
                f"Memory with id {memory.id} already exists"
            )
        self._memories.append(memory)

    async def get(self, id: UUID) -> Memory:
        for memory in self._memories:
            if memory.id == id:
                return memory
        raise MemoryNotFoundError(f"Memory with id {id} not found")

    async def authenticated_get(self, id: UUID):
        for memory in self._memories:
            if memory.id == id:
                return memory
        raise MemoryNotFoundError(f"Memory with id {id} not found")

    async def public_get(self, id: UUID) -> Memory:
        for memory in self._memories:
            if memory.id == id and memory.private is False:
                return memory
        raise MemoryNotFoundError(f"Memory with id {id} not found")

    async def authenticated_list_all(self) -> list[Memory]:
        return self._memories

    async def list_all(self, user: User) -> list[Memory]:
        """List all memories belonging to the user."""
        return [m for m in self._memories if m.owner == user.id]

    async def public_list_all(self) -> list[Memory]:
        return [m for m in self._memories if not m.private]

    async def update(self, memory: Memory) -> None:
        # changed in-mem so all we do is check if mem exists.
        await self.authenticated_get(memory.id)

    async def delete(self, memory: Memory) -> None:
        for i, m in enumerate(self._memories):
            if m.id == memory.id:
                del self._memories[i]
                return
        raise MemoryNotFoundError(f"Memory with id {memory.id} not found")

    async def update_public_private(self, memory: Memory) -> None:
        pass

    async def update_pin_status(self, memory: Memory) -> None:
        pass

    async def update_tags(self, memory: Memory) -> None:
        pass

    async def update_readers(self, memory: Memory) -> None:
        pass

    async def update_editors(self, memory: Memory) -> None:
        pass


class SupabaseMemoryRepository(AbstractMemoryRepository):
    def __init__(self, client: AsyncClient):
        self.client = client
        self.table = self.client.table("memories")

    async def get(self, id: UUID) -> Memory:
        """Get a memory by id."""
        q = self.table.select("*").eq("id", str(id))
        res = await q.execute()
        if hasattr(res, "data") and res.data:
            data = res.data[0]
            return Memory(
                id=data["id"],
                owner=data["owner"],
                readers=set(data["readers"]),
                editors=set(data["editors"]),
                title=data["title"],
                fragments=data["fragments"],
                private=data["private"],
                pinned=data["pinned"],
                tags=set(data["tags"]),
                created_at=data["created_at"],
                created_by=data["created_by"],
                updated_at=data["updated_at"],
                updated_by=data["updated_by"],
            )
        raise MemoryNotFoundError(f"Memory with id {id} not found")

    async def public_get(self, id: UUID) -> Memory:
        res = await self._get(id, authenticated=False)
        return res

    async def authenticated_get(self, id: UUID) -> Memory:
        res = await self._get(id, authenticated=True)
        return res

    async def create_empty(self, memory: Memory) -> None:
        try:
            await self.table.insert(  # type: ignore
                {
                    "id": str(memory.id),
                    "title": memory.title,
                    "owner": str(memory.owner),
                    "created_by": str(memory.created_by),
                }
            ).execute()
        except PostgrestAPIError as e:
            logger.exception(e)
            if e.code == "23505":
                raise MemoryAlreadyExistsError(e.details) from e
            else:
                raise e

    async def delete(self, memory: Memory) -> None:
        await self.table.delete().eq("id", str(memory.id)).execute()

    async def _get(self, id: UUID, authenticated: bool) -> Memory:
        q = self.table.select("*").eq("id", str(id))
        if not authenticated:
            q = q.eq("private", False)
        res = await q.execute()
        if hasattr(res, "data") and res.data:
            data = res.data[0]
            return Memory(
                id=data["id"],
                owner=data["owner"],
                readers=set(data["readers"]),
                editors=set(data["editors"]),
                title=data["title"],
                fragments=data["fragments"],
                private=data["private"],
                pinned=data["pinned"],
                tags=set(data["tags"]),
                created_at=data["created_at"],
                created_by=data["created_by"],
                updated_at=data["updated_at"],
                updated_by=data["updated_by"],
            )
        raise MemoryNotFoundError(f"Memory with id {id} not found")

    async def _list(self, authenticated: bool) -> list[Memory]:
        q = (
            self.table.select("*")
            .order("pinned", desc=True)
            .order("created_at", desc=False)
        )
        if not authenticated:
            q = q.eq("private", False)
        res = await q.execute()
        if hasattr(res, "data") and res.data:
            return [
                Memory(
                    id=data["id"],
                    owner=data["owner"],
                    readers=set(data["readers"]),
                    editors=set(data["editors"]),
                    title=data["title"],
                    fragments=data["fragments"],
                    private=data["private"],
                    pinned=data["pinned"],
                    tags=data["tags"],
                    created_at=data["created_at"],
                    created_by=data["created_by"],
                    updated_at=data["updated_at"],
                    updated_by=data["updated_by"],
                )
                for data in res.data
            ]
        return []

    async def public_list_all(self) -> list[Memory]:
        res = await self._list(authenticated=False)
        return res

    async def authenticated_list_all(self) -> list[Memory]:
        res = await self._list(authenticated=True)
        return res

    async def list_all(self, user: User) -> list[Memory]:
        """List all memories belonging to the user."""
        q = (
            self.table.select("*")
            .filter("owner", "eq", str(user.id))
            .order("pinned", desc=True)
            .order("created_at", desc=False)
        )
        res = await q.execute()
        if hasattr(res, "data") and res.data:
            return [
                Memory(
                    id=data["id"],
                    owner=data["owner"],
                    readers=set(data["readers"]),
                    editors=set(data["editors"]),
                    title=data["title"],
                    fragments=data["fragments"],
                    private=data["private"],
                    pinned=data["pinned"],
                    tags=data["tags"],
                    created_at=data["created_at"],
                    created_by=data["created_by"],
                    updated_at=data["updated_at"],
                    updated_by=data["updated_by"],
                )
                for data in res.data
            ]
        return []

    async def update(self, memory: Memory) -> None:
        await (
            self.table.update(  # type: ignore
                {
                    "fragments": [f.serialise() for f in memory.fragments],
                    "title": memory.title,
                    "updated_at": datetime.now(tz=timezone.utc).isoformat(),
                }
            )
            .eq("id", str(memory.id))
            .execute()
        )

    async def update_public_private(self, memory: Memory) -> None:
        await (
            self.table.update(  # type: ignore
                {
                    "private": memory.private,
                    "updated_at": memory.updated_at.isoformat(),
                }
            )
            .eq("id", str(memory.id))
            .execute()
        )

    async def update_pin_status(self, memory: Memory) -> None:
        await (
            self.table.update(  # type: ignore
                {
                    "pinned": memory.pinned,
                    "updated_at": memory.updated_at.isoformat(),
                }
            )
            .eq("id", str(memory.id))
            .execute()
        )

    async def update_tags(self, memory: Memory) -> None:
        await (
            self.table.update(  # type: ignore
                {
                    "tags": [tag.value for tag in memory.tags],
                    "updated_at": memory.updated_at.isoformat(),
                }
            )
            .eq("id", str(memory.id))
            .execute()
        )

    async def update_editors(self, memory: Memory) -> None:
        await (
            self.table.update(  # type: ignore
                {
                    "editors": [str(editor) for editor in memory.editors],
                    "updated_at": memory.updated_at.isoformat(),
                }
            )
            .eq("id", str(memory.id))
            .execute()
        )

    async def update_readers(self, memory: Memory) -> None:
        await (
            self.table.update(  # type: ignore
                {
                    "readers": [str(reader) for reader in memory.readers],
                    "updated_at": memory.updated_at.isoformat(),
                }
            )
            .eq("id", str(memory.id))
            .execute()
        )
