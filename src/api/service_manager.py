import logging

import supabase
from pydantic_settings import BaseSettings
from supabase import create_async_client

from events.pubsub import LocalPublisher
from events.storage_subscriber import StorageSubscriber
from memory_repository import (
    AbstractMemoryRepository,
    InMemoryMemoryRepository,
    SupabaseMemoryRepository,
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
        self.filesys_event_handler = StorageSubscriber(
            self.pub, self.memory_repo, self.ifilesys
        )
        self.filesys_event_handler.subscribe(
            [
                "filesys_save_error",
                "filesys_save_success",
                "filesys_delete_error",
                "filesys_delete_success",
            ]
        )
