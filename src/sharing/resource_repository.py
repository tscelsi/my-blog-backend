import abc
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from supabase import AsyncClient

from entities.user import User


class CedarResource(BaseModel):
    id: UUID
    owner: UUID
    editors: set[UUID]
    readers: set[UUID]
    private: bool
    _type: str = "Memory"

    def cedar_schema(self) -> dict[str, Any]:
        """Convert a Memory entity to a Cedar schema entity."""
        return {
            "uid": self.cedar_eid_json(),
            "attrs": {
                "editors": [
                    {"__entity": User(id=editor).cedar_eid_json()}
                    for editor in self.editors
                ],
                "readers": [
                    {"__entity": User(id=reader).cedar_eid_json()}
                    for reader in self.readers
                ],
                "owner": {"__entity": User(id=self.owner).cedar_eid_json()},
            },
            "parents": [],
        }

    def cedar_eid_str(self) -> str:
        """Convert the Memory entity to a Cedar EID."""
        return f'{self._type}::"{self.id}"'

    def cedar_eid_json(self) -> dict[str, str]:
        return {"id": str(self.id), "type": self._type}


class AbstractResourceRepository(abc.ABC):
    @abc.abstractmethod
    async def get_memory_resources(self) -> list[CedarResource]:
        pass


class CedarResourceInMemoryRepository(AbstractResourceRepository):
    def __init__(self, memory_resources: list[CedarResource] = []):
        self._memory_resources: dict[UUID, CedarResource] = {
            m.id: m for m in memory_resources
        }

    async def get_memory_resources(self) -> list[CedarResource]:
        resources = [m for m in self._memory_resources.values()]
        return resources


class CedarResourceRepository(AbstractResourceRepository):
    def __init__(self, client: AsyncClient):
        self.client = client

    async def get_memory_resources(self) -> list[CedarResource]:
        q = self.client.table("memories").select(
            "id", "title", "owner", "readers", "editors", "private"
        )
        response = await q.execute()
        resources = [
            CedarResource(
                id=m["id"],
                owner=m["owner"],
                editors=set(m["editors"] or []),
                readers=set(m["readers"] or []),
                private=m["private"],
            )
            for m in response.data
        ]
        return resources
