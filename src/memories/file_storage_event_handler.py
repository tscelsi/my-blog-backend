import logging
from typing import Any

import memories.services as memory_services
from memories.events import StorageEvents
from memories.memory_repository import AbstractMemoryRepository
from utils.events.pubsub import LocalPublisher, LocalSubscriber
from utils.file_storage.base_storage import AbstractFileStorage

logger = logging.getLogger(__name__)


class FileStorageEventHandler(LocalSubscriber):
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
        if topic == StorageEvents.FILESYS_SAVE_ERROR:
            memory = event["memory"]
            fragment = event["fragment"]
            await memory_services.save_file_fragment_upload_error(
                memory.id, fragment.id, self.repo
            )
        elif topic == StorageEvents.FILESYS_SAVE_SUCCESS:
            memory = event["memory"]
            fragment = event["fragment"]
            await memory_services.save_file_fragment_upload_success(
                memory.id, fragment.id, self.repo, self.storage
            )
        elif topic == StorageEvents.FILESYS_DELETE_ERROR:
            logger.error(f"Error deleting file: {event['key']}")
        elif topic == StorageEvents.FILESYS_DELETE_SUCCESS:
            logger.info(f"Successfully deleted file: {event['key']}")
