import asyncio

from sharing.exceptions import ResourceNotFoundError
from sharing.resource_repository import AbstractResourceRepository
from sharing.resources import CedarAccount, CedarMemory


class PermissionsManager:
    def __init__(self, resource_repository: AbstractResourceRepository):
        self._resource_repository = resource_repository
        self._resources: dict[str, CedarAccount | CedarMemory] = {}

    def get_resource(self, cedar_eid: str) -> CedarAccount | CedarMemory:
        r = self._resources.get(cedar_eid)
        if not r:
            raise ResourceNotFoundError(f"Resource {cedar_eid} not found")
        return r

    def update_resource(self, resource: CedarAccount | CedarMemory):
        self._resources[resource.cedar_eid_str()] = resource

    def remove_resource(self, resource_id: str):
        if resource_id in self._resources:
            del self._resources[resource_id]

    async def init(self):
        memories, accounts = await asyncio.gather(
            self._resource_repository.get_memory_resources(),
            self._resource_repository.get_account_resources(),
        )
        self._resources = {r.cedar_eid_str(): r for r in memories + accounts}
