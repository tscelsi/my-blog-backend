import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Request

import sharing.services as services
from api.middleware.auth import require_auth_dep
from api.service_manager import ServiceManager
from entities.memory import BaseMemoryError, MemoryNotFoundError
from entities.user import UserNotFoundError
from memories.memory_repository import (
    AbstractMemoryRepository,
    SupabaseMemoryRepository,
)
from sharing.authorise import authorise
from sharing.exceptions import AuthorisationError, BaseSharingError
from sharing.user_repository import (
    AbstractUserRepository,
    SupabaseUserRepository,
)

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/sharing",
    dependencies=[Depends(require_auth_dep)],
)


def get_memory_repository_dep(request: Request) -> AbstractMemoryRepository:
    """Dependency to get the request-specific memory repository."""
    repo = SupabaseMemoryRepository(request.state.supabase_client)
    return repo


def get_user_repository_dep(request: Request) -> AbstractUserRepository:
    """Dependency to get the request-specific memory repository."""
    repo = SupabaseUserRepository(request.state.supabase_client)
    return repo


def get_admin_user_repository_dep() -> AbstractUserRepository:
    """Dependency to get the request-specific memory repository."""
    sm = ServiceManager.get()
    assert sm.supabase_admin_client is not None
    repo = SupabaseUserRepository(sm.supabase_admin_client)
    return repo


def get_service_manager_dep() -> ServiceManager:
    """Dependency to get the service manager."""
    return ServiceManager.get()


@router.get("/{resource_id}/permissions", status_code=200)
async def get_permissions(
    request: Request,
    resource_id: Annotated[UUID, Path()],
    memory_repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
    user_repo: AbstractUserRepository = Depends(get_admin_user_repository_dep),
    service_manager: ServiceManager = Depends(get_service_manager_dep),
) -> services.MemoryPermissionData:
    """Get a Memory's sharing permissions."""
    try:
        authorise(
            request.user,
            'Action::"GetSharingPermissions"',
            f'Memory::"{resource_id}"',
            service_manager,
        )
    except AuthorisationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    try:
        permissions = await services.get_permissions(
            resource_id, memory_repo, user_repo
        )
        return permissions
    except MemoryNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{resource_id}/editors/add", status_code=204)
async def add_editor(
    request: Request,
    resource_id: Annotated[UUID, Path()],
    email: Annotated[str, Body(embed=True)],
    memory_repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
    user_repo: AbstractUserRepository = Depends(get_admin_user_repository_dep),
    service_manager: ServiceManager = Depends(get_service_manager_dep),
):
    """Add a user to a Memory's edit permissions."""
    try:
        authorise(
            request.user,
            'Action::"EditShare"',
            f'Memory::"{resource_id}"',
            service_manager,
        )
    except AuthorisationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    try:
        await services.add_editor(
            request.user,
            resource_id,
            email,
            memory_repo,
            user_repo,
            service_manager.pub,
        )
    except (MemoryNotFoundError, UserNotFoundError, BaseSharingError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{resource_id}/editors/remove", status_code=204)
async def remove_editor(
    request: Request,
    resource_id: Annotated[UUID, Path()],
    user_id: Annotated[UUID, Body(embed=True)],
    memory_repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
    service_manager: ServiceManager = Depends(get_service_manager_dep),
):
    """Remove a user from a Memory's edit permissions."""
    try:
        authorise(
            request.user,
            'Action::"EditShare"',
            f'Memory::"{resource_id}"',
            service_manager,
        )
    except AuthorisationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    try:
        await services.remove_editor(
            resource_id,
            user_id,
            memory_repo,
            service_manager.pub,
        )
    except AuthorisationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except (MemoryNotFoundError, UserNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{resource_id}/readers/add", status_code=204)
async def add_reader(
    request: Request,
    resource_id: Annotated[UUID, Path()],
    email: Annotated[str, Body(embed=True)],
    memory_repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
    user_repo: AbstractUserRepository = Depends(get_admin_user_repository_dep),
    service_manager: ServiceManager = Depends(get_service_manager_dep),
):
    """Add a user to a Memory's read permissions."""
    try:
        authorise(
            request.user,
            'Action::"EditShare"',
            f'Memory::"{resource_id}"',
            service_manager,
        )
    except AuthorisationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    try:
        await services.add_reader(
            request.user,
            resource_id,
            email,
            memory_repo,
            user_repo,
            service_manager.pub,
        )
    except AuthorisationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except (MemoryNotFoundError, UserNotFoundError, BaseSharingError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{resource_id}/readers/remove", status_code=204)
async def remove_reader(
    request: Request,
    resource_id: Annotated[UUID, Path()],
    user_id: Annotated[UUID, Body(embed=True)],
    memory_repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
    service_manager: ServiceManager = Depends(get_service_manager_dep),
):
    """Remove a user from a Memory's read permissions."""
    try:
        authorise(
            request.user,
            'Action::"EditShare"',
            f'Memory::"{resource_id}"',
            service_manager,
        )
    except AuthorisationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    try:
        await services.remove_reader(
            resource_id,
            user_id,
            memory_repo,
            service_manager.pub,
        )
    except AuthorisationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except (MemoryNotFoundError, UserNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{resource_id}/set-public", status_code=204)
async def set_public_private_endpoint(
    request: Request,
    resource_id: Annotated[UUID, Path()],
    is_public: Annotated[bool, Body(embed=True)],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
    service_manager: ServiceManager = Depends(get_service_manager_dep),
):
    """Mark a memory as private or public."""
    try:
        authorise(
            request.user,
            'Action::"EditShare"',
            f'Memory::"{resource_id}"',
            service_manager,
        )
    except AuthorisationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    try:
        if is_public:
            await services.make_memory_public(
                resource_id, repo, service_manager.pub
            )
        else:
            await services.make_memory_private(
                resource_id, repo, service_manager.pub
            )
    except (BaseMemoryError, BaseSharingError) as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error marking memory as draft: {e}")
        logger.exception(e)
        return HTTPException(
            status_code=500, detail="Error marking memory as draft"
        )
