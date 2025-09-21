import logging

import supabase
from pydantic_settings import BaseSettings
from supabase import create_async_client

from memories.events import StorageEvents
from memories.file_storage_event_handler import FileStorageEventHandler
from memories.memory_repository import (
    AbstractMemoryRepository,
    SupabaseMemoryRepository,
)
from sharing.events import PermissionsEvents
from sharing.permissions_event_handler import PermissionsEventHandler
from sharing.permissions_manager import PermissionsManager
from sharing.resource_repository import (
    AbstractResourceRepository,
    CedarResourceRepository,
)
from utils.background_tasks import BackgroundTasks
from utils.events.pubsub import LocalPublisher
from utils.file_storage.base_storage import AbstractFileStorage
from utils.file_storage.fake_storage import FakeStorage
from utils.file_storage.supabase_storage import SupabaseStorage

logger = logging.getLogger(__name__)


class SupabaseSettings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str


def gen_fake_storage():
    return FakeStorage(bucket="euw2.meapp.t0mm08669.develop")


class ServiceManager:
    service_manager: "ServiceManager | None" = None

    def __init__(
        self,
        memory_repository: AbstractMemoryRepository | None = None,
        storage_interface: AbstractFileStorage | None = FakeStorage(
            bucket="euw2.meapp.t0mm08669.develop"
        ),
        permissions_repository: AbstractResourceRepository | None = None,
    ):
        self.storage_interface = storage_interface
        self.supabase_admin_client = None
        self.memory_repository = memory_repository
        self.permissions_repository = permissions_repository
        self.background_tasks = BackgroundTasks()
        self.pub = LocalPublisher()
        self.supabase_settings = SupabaseSettings()  # type: ignore

    @staticmethod
    def get(
        memory_repository: AbstractMemoryRepository | None = None,
        storage_interface: AbstractFileStorage | None = None,
        permissions_repository: AbstractResourceRepository | None = None,
    ):
        """Retrieve the service manager singleton instance."""
        if ServiceManager.service_manager is None:
            # Create the singleton instance if it doesn't exist
            ServiceManager.service_manager = ServiceManager(
                memory_repository,
                permissions_repository=permissions_repository,
                storage_interface=storage_interface,
            )
        return ServiceManager.service_manager

    def get_memory_repository(self) -> AbstractMemoryRepository:
        """Get the memory repository."""
        if self.memory_repository is None:
            raise ValueError("Memory repository not initialized.")
        return self.memory_repository

    def get_supabase_client(self) -> supabase.AsyncClient:
        """Get the Supabase client."""
        if self.supabase_admin_client is None:
            raise ValueError("Supabase client not initialized.")
        return self.supabase_admin_client

    def get_storage(self) -> AbstractFileStorage:
        """Get the file system storage."""
        if self.storage_interface is None:
            raise ValueError("File system storage not initialized.")
        return self.storage_interface

    async def start(self):
        self.supabase_admin_client = await create_async_client(
            supabase_url="https://tzppymbakxwelmkouucs.supabase.co",
            supabase_key=self.supabase_settings.SUPABASE_KEY,
        )
        self.memory_repository = (
            self.memory_repository
            if self.memory_repository is not None
            else SupabaseMemoryRepository(self.supabase_admin_client)
        )
        self.storage_interface = (
            self.storage_interface
            if self.storage_interface is not None
            else SupabaseStorage(
                bucket="memories.develop", client=self.supabase_admin_client
            )
        )

        # permissions setup #
        self.permissions_repository = (
            self.permissions_repository
            if self.permissions_repository is not None
            else CedarResourceRepository(self.supabase_admin_client)
        )
        self.permissions_manager = PermissionsManager(
            self.permissions_repository
        )
        await self.permissions_manager.init()

        # events
        self.storage_event_handler = FileStorageEventHandler(
            self.pub, self.memory_repository, self.storage_interface
        )
        self.permissions_event_handler = PermissionsEventHandler(
            self.pub, self.permissions_manager
        )
        self.storage_event_handler.subscribe([x for x in StorageEvents])
        self.permissions_event_handler.subscribe(
            [x for x in PermissionsEvents]
        )
