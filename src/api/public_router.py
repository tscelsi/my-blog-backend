"""A public router, for un-authenticated access."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from api.service_manager import ServiceManager
from entities.memory import Memory, MemoryNotFoundError
from memories import services
from memories.memory_repository import (
    AbstractMemoryRepository,
    SupabaseMemoryRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public")


def get_memory_repository_dep() -> AbstractMemoryRepository:
    """Dependency to get a memory repository instance using the supabase admin
    client."""
    sm = ServiceManager.get()
    assert sm.supabase_admin_client is not None
    return SupabaseMemoryRepository(sm.supabase_admin_client)


def get_service_manager_dep() -> ServiceManager:
    """Dependency to get the service manager."""
    return ServiceManager.get()


@router.get("/memory/{memory_id}", response_model=Memory, status_code=200)
async def get_memory(
    memory_id: UUID,
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
    service_manager: ServiceManager = Depends(get_service_manager_dep),
) -> Memory:
    """Get a public memory."""
    try:
        memory = await services.get_memory(
            memory_id, repo, service_manager.get_filesys()
        )
    except MemoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")
    if memory.private:
        raise HTTPException(status_code=403, detail="Memory is private")
    return memory
