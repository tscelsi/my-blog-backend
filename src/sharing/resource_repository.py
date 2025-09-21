import abc
from uuid import UUID

from supabase import AsyncClient

from sharing.resources import CedarAccount, CedarMemory


class AbstractResourceRepository(abc.ABC):
    @abc.abstractmethod
    async def get_memory_resources(self) -> list[CedarMemory]:
        pass

    @abc.abstractmethod
    async def get_account_resources(self) -> list[CedarAccount]:
        pass


class CedarResourceInMemoryRepository(AbstractResourceRepository):
    def __init__(
        self,
        memory_resources: list[CedarMemory] = [],
        account_resources: list[CedarAccount] = [],
    ):
        self._memory_resources: dict[UUID, CedarMemory] = {
            m.id: m for m in memory_resources
        }
        self.account_resources: dict[UUID, CedarAccount] = {
            acc.id: acc for acc in account_resources
        }

    async def get_memory_resources(self) -> list[CedarMemory]:
        resources = [m for m in self._memory_resources.values()]
        return resources

    async def get_account_resources(self) -> list[CedarAccount]:
        resources = [acc for acc in self.account_resources.values()]
        return resources


class CedarResourceRepository(AbstractResourceRepository):
    def __init__(self, client: AsyncClient):
        self.client = client

    async def get_memory_resources(self) -> list[CedarMemory]:
        q = self.client.table("memories").select(
            "id", "title", "owner", "readers", "editors", "private"
        )
        response = await q.execute()
        resources = [
            CedarMemory(
                id=m["id"],
                owner=m["owner"],
                editors=m["editors"],
                readers=m["readers"],
                private=m["private"],
            )
            for m in response.data
        ]
        return resources

    async def get_account_resources(self) -> list[CedarAccount]:
        q = self.client.table("accounts").select("id", "owner")
        response = await q.execute()
        resources = [
            CedarAccount(id=m["id"], owner=m["owner"]) for m in response.data
        ]
        return resources
