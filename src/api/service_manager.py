import logging

import supabase
from pydantic_settings import BaseSettings
from supabase import create_async_client

from events.event_defs import StorageEvents
from events.file_storage_event_handler import FileStorageEventHandler
from events.pubsub import LocalPublisher
from memory_repository import (
    AbstractMemoryRepository,
    InMemoryMemoryRepository,
    SupabaseMemoryRepository,
)
from sharing.events import PermissionsEvents
from sharing.permissions_event_handler import PermissionsEventHandler
from sharing.permissions_manager import PermissionsManager
from sharing.resource_repository import (
    CedarResourceInMemoryRepository,
    CedarResourceRepository,
)
from utils.background_tasks import BackgroundTasks
from utils.file_storage.fake_storage import FakeStorage
from utils.file_storage.supabase_storage import SupabaseStorage

logger = logging.getLogger(__name__)


class SupabaseSettings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str


class ServiceManager:
    service_manager: "ServiceManager | None" = None

    def __init__(self, stub: bool = False):
        self.stub = stub
        self.ifilesys = None
        self.supabase_client = None
        self.memory_repo = None
        self.filesys_event_handler = None
        self.background_tasks = BackgroundTasks()
        self.pub = LocalPublisher()
        self.supabase_settings = SupabaseSettings()  # type: ignore

    @staticmethod
    def get(stub: bool = False):
        """Retrieve the service manager singleton instance."""
        if ServiceManager.service_manager is None:
            # Create the singleton instance if it doesn't exist
            ServiceManager.service_manager = ServiceManager(stub=stub)
        return ServiceManager.service_manager

    def get_memory_repository(self) -> AbstractMemoryRepository:
        """Get the memory repository."""
        if self.memory_repo is None:
            raise ValueError("Memory repository not initialized.")
        return self.memory_repo

    def get_supabase_client(self) -> supabase.AsyncClient:
        """Get the Supabase client."""
        if self.supabase_client is None:
            raise ValueError("Supabase client not initialized.")
        return self.supabase_client

    def get_filesys(self) -> FakeStorage | SupabaseStorage:
        """Get the file system storage."""
        if self.ifilesys is None:
            raise ValueError("File system storage not initialized.")
        return self.ifilesys

    async def start(self):
        self.supabase_client = await create_async_client(
            supabase_url="https://tzppymbakxwelmkouucs.supabase.co",
            supabase_key=self.supabase_settings.SUPABASE_KEY,
        )
        self.memory_repo = (
            InMemoryMemoryRepository()
            if self.stub
            else SupabaseMemoryRepository(self.supabase_client)
        )
        self.ifilesys = (
            FakeStorage(bucket="euw2.meapp.t0mm08669.develop")
            if self.stub
            else SupabaseStorage(
                bucket="memories.develop", client=self.supabase_client
            )
        )
        self.filesys_event_handler = FileStorageEventHandler(
            self.pub, self.memory_repo, self.ifilesys
        )
        self.filesys_event_handler.subscribe([x for x in StorageEvents])

        # permissions setup #
        self.permission_resource_repo = (
            CedarResourceInMemoryRepository()
            if self.stub
            else CedarResourceRepository(self.supabase_client)
        )
        self.permissions_manager = PermissionsManager(
            self.permission_resource_repo
        )
        await self.permissions_manager.init()
        self.permissions_event_handler = PermissionsEventHandler(
            self.pub, self.permissions_manager
        )
        self.permissions_event_handler.subscribe(
            [x for x in PermissionsEvents]
        )
