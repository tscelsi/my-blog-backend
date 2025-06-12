"""A public router for everyone to use. No auth needed."""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from api.service_manager import ServiceManager
from memory import Memory, MemoryNotFoundError
from memory_repository import (
    AbstractMemoryRepository,
    SupabaseMemoryRepository,
)
from tags import Tag

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/public")


def get_memory_repository_dep(request: Request) -> AbstractMemoryRepository:
    """Dependency to get the request-specific memory repository.

    Uses the service manager's generic supabase client, that doesn't contain
    a user-specific authorization header."""
    service_manager = ServiceManager.get(stub=False)
    repo = SupabaseMemoryRepository(service_manager.get_supabase_client())
    return repo


class ListMemoryResponse(BaseModel):
    id: UUID
    title: str
    pinned: bool
    private: bool
    created_at: datetime


@router.get(
    "/memory", response_model=list[ListMemoryResponse], status_code=200
)
async def list_memories(
    request: Request,
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
):
    """List all my memories."""
    if request.user.is_authenticated:
        memories = await repo.authenticated_list_all()
    else:
        memories = await repo.public_list_all()
    return memories


@router.get("/memory/{memory_id}", response_model=Memory, status_code=200)
async def get_memory(
    memory_id: UUID,
    request: Request,
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
):
    """Get a memory."""
    try:
        if request.user.is_authenticated:
            memory = await repo.authenticated_get(memory_id)
        else:
            memory = await repo.public_get(memory_id)
    except MemoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")
    return memory


@router.get("/tags", response_model=list[Tag], status_code=200)
async def list_tags():
    """List all available tags."""
    return [t for t in Tag.__members__.values()]
