import logging
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from pydantic import BaseModel

import memories.services as memory_services
from api.middleware.auth import require_auth_dep
from api.service_manager import ServiceManager
from entities.fragments.base import FragmentType
from entities.fragments.text import Op
from memories.memory_repository import (
    AbstractMemoryRepository,
    SupabaseMemoryRepository,
)
from sharing.exceptions import AuthorisationError
from utils.authorise import authorise

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/fragment",
    dependencies=[Depends(require_auth_dep)],
)


def get_memory_repository_dep(request: Request) -> AbstractMemoryRepository:
    """Dependency to get the request-specific memory repository."""
    repo = SupabaseMemoryRepository(request.state.supabase_client)
    return repo


def get_service_manager_dep() -> ServiceManager:
    """Dependency to get the service manager."""
    return ServiceManager.get()


class Response(BaseModel):
    fragment_id: UUID


@router.post("/file", status_code=201, response_model=Response)
async def add_file_fragment_to_memory_endpoint(
    request: Request,
    file: Annotated[UploadFile, File()],
    memory_id: Annotated[UUID, Form()],
    type: Annotated[FragmentType, Form()],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
    service_manager: ServiceManager = Depends(get_service_manager_dep),
) -> Response:
    """Add a file Fragment to a Memory."""
    try:
        authorise(
            request.user,
            'Action::"CreateFragment"',
            f'Memory::"{memory_id}"',
            service_manager,
        )
    except AuthorisationError as e:
        logger.error(f"Authorisation error: {e.detail}")
        raise HTTPException(status_code=403, detail=str(e))
    try:
        fragment_id = await memory_services.add_file_fragment_to_memory(
            memory_id,
            type,
            file.filename or "_blank",
            file.file,
            service_manager.get_storage(),
            repo,
            service_manager.background_tasks,
            service_manager.pub,
        )
        return Response(fragment_id=fragment_id)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while adding a fragment to a memory.",
        )


@router.post("/rich-text", status_code=201, response_model=Response)
async def add_rich_text_fragment_to_memory_endpoint(
    request: Request,
    content: Annotated[list[Op], Body()],
    memory_id: Annotated[UUID, Body()],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
    service_manager: ServiceManager = Depends(get_service_manager_dep),
) -> Response:
    """Add a rich text Fragment to a Memory."""
    try:
        authorise(
            request.user,
            'Action::"CreateFragment"',
            f'Memory::"{memory_id}"',
            service_manager,
        )
    except AuthorisationError as e:
        logger.error(f"Authorisation error: {e.detail}")
        raise HTTPException(status_code=403, detail=str(e))
    try:
        fragment_id = await memory_services.add_rich_text_fragment_to_memory(
            memory_id, content, repo
        )
        return Response(fragment_id=fragment_id)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while adding a fragment to a memory.",
        )


@router.put("/rich-text", status_code=201, response_model=Response)
async def modify_rich_text_fragment_endpoint(
    request: Request,
    content: Annotated[list[Op], Body()],
    memory_id: Annotated[UUID, Body()],
    fragment_id: Annotated[UUID, Body()],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
    service_manager: ServiceManager = Depends(get_service_manager_dep),
) -> Response:
    """Modify an existing rich text Fragment."""
    try:
        authorise(
            request.user,
            'Action::"UpdateFragment"',
            f'Memory::"{memory_id}"',
            service_manager,
        )
    except AuthorisationError as e:
        logger.error(f"Authorisation error: {e.detail}")
        raise HTTPException(status_code=403, detail=str(e))
    try:
        fragment_id = await memory_services.modify_rich_text_fragment(
            memory_id, fragment_id, content, repo
        )
        return Response(fragment_id=fragment_id)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while modifying the fragment.",
        )


@router.post("/rss", status_code=201, response_model=Response)
async def add_rss_feed_fragment_to_memory_endpoint(
    request: Request,
    urls: Annotated[list[str], Body()],
    memory_id: Annotated[UUID, Body()],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
    service_manager: ServiceManager = Depends(get_service_manager_dep),
) -> Response:
    """Add an RSS feed Fragment to a Memory."""
    try:
        authorise(
            request.user,
            'Action::"CreateFragment"',
            f'Memory::"{memory_id}"',
            service_manager,
        )
    except AuthorisationError as e:
        logger.error(f"Authorisation error: {e.detail}")
        raise HTTPException(status_code=403, detail=str(e))
    try:
        fragment_id = await memory_services.add_rss_feed_to_memory(
            memory_id, urls, repo
        )
        return Response(fragment_id=fragment_id)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while adding a fragment to a memory.",
        )


@router.put("/rss", status_code=201, response_model=Response)
async def modify_rss_feed_fragment_endpoint(
    request: Request,
    urls: Annotated[list[str], Body()],
    memory_id: Annotated[UUID, Body()],
    fragment_id: Annotated[UUID, Body()],
    n_items: Annotated[int | None, Body()] = None,
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
    service_manager: ServiceManager = Depends(get_service_manager_dep),
) -> Response:
    """Add an RSS feed Fragment to a Memory."""
    try:
        authorise(
            request.user,
            'Action::"UpdateFragment"',
            f'Memory::"{memory_id}"',
            service_manager,
        )
    except AuthorisationError as e:
        logger.error(f"Authorisation error: {e.detail}")
        raise HTTPException(status_code=403, detail=str(e))
    try:
        fragment_id = await memory_services.modify_rss_feed_fragment(
            memory_id, fragment_id, urls, repo, n_items=n_items
        )
        return Response(fragment_id=fragment_id)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while modifying an RSS fragment.",
        )
