from uuid import uuid4

from events.pubsub import LocalPublisher
from sharing.events import PermissionsEvents
from sharing.permissions_event_handler import PermissionsEventHandler
from sharing.permissions_manager import PermissionsManager
from sharing.resource_repository import AbstractResourceRepository
from test.fixtures import create_memory


async def test_handle_skips_when_not_permission_event(
    pub: LocalPublisher, resource_repo: AbstractResourceRepository
):
    mgr = PermissionsManager(resource_repo)
    handler = PermissionsEventHandler(pub, mgr)
    await handler.handle({"topic": "some_event", "memory": "memory"})
    assert not handler.has_handled_event


async def test_handle_skips_when_permission_event(
    pub: LocalPublisher, resource_repo: AbstractResourceRepository
):
    mgr = PermissionsManager(resource_repo)
    handler = PermissionsEventHandler(pub, mgr)
    await handler.handle(
        {"topic": PermissionsEvents.EDITORS_ADDED, "memory": create_memory()}
    )
    assert handler.has_handled_event
    assert len(mgr._resources) == 1  # type: ignore


async def test_handle_replaces_memory_in_manager_with_updated_fields(
    pub: LocalPublisher,
    resource_repo: AbstractResourceRepository,
):
    mgr = PermissionsManager(resource_repo)
    handler = PermissionsEventHandler(pub, mgr)
    mem = create_memory()
    await handler.handle(
        {"topic": PermissionsEvents.MEMORY_CREATED, "memory": mem}
    )
    assert len(mgr._resources[f'Memory::"{mem.id}"'].editors) == 0  # type: ignore # noqa
    mem.add_editor(uuid4())
    await handler.handle(
        {"topic": PermissionsEvents.EDITORS_ADDED, "memory": mem}
    )
    assert handler.has_handled_event
    assert len(mgr._resources) == 1  # type: ignore
    assert len(mgr._resources[f'Memory::"{mem.id}"'].editors) == 1  # type: ignore # noqa
