import logging
from typing import Any

import services
from events.pubsub import LocalPublisher, LocalSubscriber
from memory_repository import AbstractMemoryRepository
from utils.file_storage.base_storage import AbstractFileStorage

logger = logging.getLogger(__name__)


class StorageSubscriber(LocalSubscriber):
    """A subscriber concerned with file manipulation events."""

    def __init__(
        self,
        publisher: LocalPublisher,
        repo: AbstractMemoryRepository,
        storage: AbstractFileStorage,
    ):
        super().__init__(publisher)
        self.repo = repo
        self.storage = storage

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
        if topic == "filesys_save_error":
            memory = event["memory"]
            fragment = event["fragment"]
            await services.save_file_fragment_upload_error(
                memory.id, fragment.id, self.repo
            )
        elif topic == "filesys_save_success":
            memory = event["memory"]
            fragment = event["fragment"]
            await services.save_file_fragment_upload_success(
                memory.id, fragment.id, self.repo, self.storage
            )
        elif topic == "filesys_delete_error":
            logger.error(f"Error deleting file: {event['key']}")
        elif topic == "filesys_delete_success":
            logger.info(f"Successfully deleted file: {event['key']}")
