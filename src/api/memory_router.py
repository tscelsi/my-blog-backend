import logging
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Request
from pydantic import BaseModel

import memories.services as services
from api.middleware.auth import require_auth_dep
from api.service_manager import ServiceManager
from entities.memory import (
    BaseMemoryError,
    Memory,
    MemoryAlreadyExistsError,
    MemoryNotFoundError,
)
from memories.memory_repository import (
    AbstractMemoryRepository,
    SupabaseMemoryRepository,
)
from sharing.authorise import authorise
from sharing.exceptions import AuthorisationError
from tags import Tag

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/memory",
    dependencies=[Depends(require_auth_dep)],
)


def get_memory_repository_dep(request: Request) -> AbstractMemoryRepository:
    """Dependency to get the request-specific memory repository."""
    repo = SupabaseMemoryRepository(request.state.supabase_client)
    return repo


def get_service_manager_dep() -> ServiceManager:
    """Dependency to get the service manager."""
    return ServiceManager.get()


class CreateMemoryResponse(BaseModel):
    id: UUID


@router.post("", response_model=CreateMemoryResponse, status_code=201)
async def create_empty_memory(
    request: Request,
    memory_title: Annotated[str, Body()] = "blank_",
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
    service_manager: ServiceManager = Depends(get_service_manager_dep),
) -> CreateMemoryResponse:
    """Create an empty memory."""
    try:
        new_memory_id = await services.create_empty_memory(
            request.user, memory_title, repo, service_manager.pub
        )
    except MemoryAlreadyExistsError:
        raise HTTPException(status_code=400, detail="Memory already exists.")
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the memory.",
        )
    return CreateMemoryResponse(id=new_memory_id)


class ListMemoryResponse(BaseModel):
    id: UUID
    title: str
    pinned: bool
    private: bool
    created_at: datetime


@router.get("", response_model=list[ListMemoryResponse], status_code=200)
async def list_user_memories(
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
):
    """List a user's memories."""
    try:
        memories = await services.list_memories(repo)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the memory.",
        )
    return memories


@router.get("/{memory_id}", response_model=Memory, status_code=200)
async def get_memory(
    request: Request,
    memory_id: UUID,
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
    service_manager: ServiceManager = Depends(get_service_manager_dep),
):
    """Get a memory."""
    try:
        authorise(
            request.user,
            'Action::"GetMemory"',
            f'Memory::"{memory_id}"',
            service_manager,
        )
    except AuthorisationError as e:
        logger.error(f"Authorisation error: {e.detail}")
        raise HTTPException(status_code=403, detail=str(e))
    try:
        memory = await services.get_memory(
            memory_id, repo, service_manager.get_filesys()
        )
    except MemoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")
    return memory


@router.post("/{memory_id}/forget", status_code=204)
async def forget_memory(
    request: Request,
    memory_id: Annotated[UUID, Path()],
    fragment_ids: Annotated[list[UUID] | None, Body(embed=True)] = None,
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
    service_manager: ServiceManager = Depends(get_service_manager_dep),
):
    """Forget a memory, or fragments of a memory."""
    try:
        if not fragment_ids:
            try:
                authorise(
                    request.user,
                    'Action::"DeleteMemory"',
                    f'Memory::"{memory_id}"',
                    service_manager,
                )
            except AuthorisationError as e:
                logger.error(f"Authorisation error: {e.detail}")
                raise HTTPException(status_code=403, detail=str(e))
            await services.forget_memory(
                memory_id,
                service_manager.get_filesys(),
                repo,
                service_manager.background_tasks,
                service_manager.pub,
            )
        else:
            try:
                authorise(
                    request.user,
                    'Action::"DeleteFragment"',
                    f'Memory::"{memory_id}"',
                    service_manager,
                )
            except AuthorisationError as e:
                logger.error(f"Authorisation error: {e.detail}")
                raise HTTPException(status_code=403, detail=str(e))
            await services.forget_fragments(
                memory_id,
                fragment_ids,
                service_manager.get_filesys(),
                repo,
                service_manager.background_tasks,
                service_manager.pub,
            )
    except BaseMemoryError as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error forgetting memory: {e}")
        logger.exception(e)
        return HTTPException(status_code=500, detail="Error forgetting memory")


@router.put("/{memory_id}/set-pin", status_code=204)
async def pin_memory(
    request: Request,
    memory_id: Annotated[UUID, Path()],
    pin: Annotated[bool, Body(embed=True)],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
    service_manager: ServiceManager = Depends(get_service_manager_dep),
):
    """Pin or unpin a memory."""
    try:
        authorise(
            request.user,
            'Action::"EditPin"',
            f'Memory::"{memory_id}"',
            service_manager,
        )
    except AuthorisationError as e:
        logger.error(f"Authorisation error: {e.detail}")
        raise HTTPException(status_code=403, detail=str(e))
    try:
        if pin:
            await services.pin_memory(memory_id, repo)
        else:
            await services.unpin_memory(memory_id, repo)
    except BaseMemoryError as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error pinning memory: {e}")
        logger.exception(e)
        return HTTPException(status_code=500, detail="Error pinning memory")


@router.put("/{memory_id}/set-tags", status_code=204)
async def tag_memory(
    request: Request,
    memory_id: Annotated[UUID, Path()],
    tags: Annotated[set[Tag], Body(embed=True)],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
    service_manager: ServiceManager = Depends(get_service_manager_dep),
):
    """Tag a memory."""
    try:
        authorise(
            request.user,
            'Action::"EditTags"',
            f'Memory::"{memory_id}"',
            service_manager,
        )
    except AuthorisationError as e:
        logger.error(f"Authorisation error: {e.detail}")
        raise HTTPException(status_code=403, detail=str(e))
    try:
        await services.update_tags(memory_id, tags, repo)
    except BaseMemoryError as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error tagging memory: {e}")
        logger.exception(e)
        return HTTPException(status_code=500, detail="Error tagging memory")


@router.put("/{memory_id}/set-fragment-order", status_code=204)
async def set_fragment_ordering(
    request: Request,
    memory_id: Annotated[UUID, Path()],
    fragment_ids: Annotated[list[UUID], Body(embed=True)],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
    service_manager: ServiceManager = Depends(get_service_manager_dep),
):
    """Update ordering of fragments in a Memory."""
    try:
        authorise(
            request.user,
            'Action::"UpdateFragmentOrder"',
            f'Memory::"{memory_id}"',
            service_manager,
        )
    except AuthorisationError as e:
        logger.error(f"Authorisation error: {e.detail}")
        raise HTTPException(status_code=403, detail=str(e))
    try:
        await services.update_memory_fragment_ordering(
            memory_id, fragment_ids, repo
        )
    except BaseMemoryError as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error re-ordering fragments: {e}")
        logger.exception(e)
        return HTTPException(
            status_code=500, detail="Error re-ordering fragments"
        )


@router.put("/{memory_id}/set-memory-title", status_code=204)
async def set_memory_title(
    request: Request,
    memory_id: Annotated[UUID, Path()],
    memory_title: Annotated[str, Body(embed=True)],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
    service_manager: ServiceManager = Depends(get_service_manager_dep),
):
    """Change a memories title."""
    try:
        authorise(
            request.user,
            'Action::"UpdateMemoryTitle"',
            f'Memory::"{memory_id}"',
            service_manager,
        )
    except AuthorisationError as e:
        logger.error(f"Authorisation error: {e.detail}")
        raise HTTPException(status_code=403, detail=str(e))
    try:
        await services.update_memory_title(
            request.user, memory_id, memory_title, repo
        )
    except BaseMemoryError as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error changing memory title: {e}")
        logger.exception(e)
        return HTTPException(
            status_code=500, detail="Error changing memory title"
        )
