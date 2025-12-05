import asyncio
import logging

from memories.memory_repository import AbstractMemoryRepository

logger = logging.getLogger(__name__)


async def ping_supabase(memory_repository: AbstractMemoryRepository) -> bool:
    """Ping the Supabase memory repository to stop project from pausing."""
    while True:
        logger.info("Pinging Supabase to keep the project awake.")
        await memory_repository.authenticated_list_all()
        logger.info("Pinged Supabase successfully.")
        await asyncio.sleep(60 * 60 * 24)  # Ping every 24 hours
