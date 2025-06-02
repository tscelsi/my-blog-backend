"""A public router for everyone to use. No auth needed."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from api.service_manager import ServiceManager
from memory import Memory
from memory_repository import (
    AbstractMemoryRepository,
    SupabaseMemoryRepository,
)

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
    created_at: datetime


@router.get(
    "/memory", response_model=list[ListMemoryResponse], status_code=200
)
async def list_memories(
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
):
    """List all my memories."""
    memories = await repo.list_all()
    return memories


@router.get("/memory/{memory_id}", response_model=Memory, status_code=200)
async def get_memory(
    memory_id: UUID,
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
):
    """Get a memory."""
    memory = await repo.get(memory_id)
    return memory
