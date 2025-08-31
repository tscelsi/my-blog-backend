from entities.memory import Memory
from sharing.exceptions import ResourceNotFoundError
from sharing.resource_repository import (
    AbstractResourceRepository,
    CedarResource,
)


class PermissionsManager:
    def __init__(self, resource_repository: AbstractResourceRepository):
        self._resource_repository = resource_repository
        self._resources: dict[str, CedarResource] = {}

    def get_resource(self, cedar_eid: str) -> CedarResource:
        r = self._resources.get(cedar_eid)
        if not r:
            raise ResourceNotFoundError(f"Resource {cedar_eid} not found")
        return r

    def update_resource(self, resource: Memory):
        self._resources[resource.cedar_eid_str()] = CedarResource(
            id=resource.id,
            owner=resource.owner,
            editors=resource.editors,
            readers=resource.readers,
            private=resource.private,
        )

    def remove_resource(self, resource_id: str):
        if resource_id in self._resources:
            del self._resources[resource_id]

    async def init(self):
        result = await self._resource_repository.get_memory_resources()
        self._resources = {r.cedar_eid_str(): r for r in result}
