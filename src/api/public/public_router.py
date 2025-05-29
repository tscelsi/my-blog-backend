"""A public router for everyone to use. No auth needed."""

from fastapi import APIRouter, Depends, Request

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


@router.get("/list-memories", response_model=list[Memory], status_code=200)
async def list_memories(
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
):
    """List all my memories."""
    memories = await repo.list_all()
    return memories
