import logging
from typing import Any

from events.pubsub import LocalPublisher, LocalSubscriber

from .events import PermissionsEvents
from .permissions_manager import PermissionsManager

logger = logging.getLogger(__name__)


class PermissionsEventHandler(LocalSubscriber):
    """A subscriber concerned with permissions events."""

    def __init__(
        self,
        publisher: LocalPublisher,
        permissions_manager: PermissionsManager,
    ):
        super().__init__(publisher)
        self._permissions_manager = permissions_manager
        self.has_handled_event = False

    async def handle(self, event: dict[str, Any]):
        """Handle incoming file manipulation events.

        Args:
            event (dict[str, Any]): The event to handle.

        Events:
            `filesys_save_error`: Updates the FileFragment on upload fail.
            `filesys_save_success`: Updates the FileFragment on upload
                success.
            `filesys_delete_error`: Logs an error message on delete fail.
            `filesys_delete_success`: Logs a success message on delete.
        """
        topic = event["topic"]
        if topic == PermissionsEvents.MEMORY_REMOVED:
            self._permissions_manager.remove_resource(event["memory"].id)
            self.has_handled_event = True
        elif topic in PermissionsEvents:
            self._permissions_manager.update_resource(event["memory"])
            self.has_handled_event = True
