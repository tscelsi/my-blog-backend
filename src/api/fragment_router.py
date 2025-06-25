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

import services
from api.middleware.auth import require_auth_dep
from api.service_manager import ServiceManager
from fragments.base import FragmentType
from fragments.text import Op
from memory_repository import (
    AbstractMemoryRepository,
    SupabaseMemoryRepository,
)

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/fragment",
    dependencies=[Depends(require_auth_dep)],
)


def get_memory_repository_dep(request: Request) -> AbstractMemoryRepository:
    """Dependency to get the request-specific memory repository."""
    repo = SupabaseMemoryRepository(request.state.supabase_client)
    return repo


@router.post("/add-file", status_code=201, response_model=None)
async def add_file_fragment_to_memory_endpoint(
    file: Annotated[UploadFile, File()],
    memory_id: Annotated[UUID, Form()],
    type: Annotated[FragmentType, Form()],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
) -> None:
    """Add a file Fragment to a Memory."""
    service_manager = ServiceManager.get()
    try:
        await services.add_file_fragment_to_memory(
            memory_id,
            type,
            file.filename or "_blank",
            file.file,
            service_manager.get_filesys(),
            repo,
            service_manager.background_tasks,
            service_manager.pub,
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while adding a fragment to a memory.",
        )


@router.post("/add-rich-text", status_code=201, response_model=None)
async def add_rich_text_fragment_to_memory_endpoint(
    content: Annotated[list[Op], Body()],
    memory_id: Annotated[UUID, Body()],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
) -> None:
    """Add a rich text Fragment to a Memory."""
    try:
        await services.add_rich_text_fragment_to_memory(
            memory_id, content, repo
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while adding a fragment to a memory.",
        )


@router.post("/modify-rich-text", status_code=201, response_model=None)
async def modify_rich_text_fragment_endpoint(
    content: Annotated[list[Op], Body()],
    memory_id: Annotated[UUID, Body()],
    fragment_id: Annotated[UUID, Body()],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
) -> None:
    """Modify an existing rich text Fragment."""
    try:
        await services.modify_rich_text_fragment(
            memory_id, fragment_id, content, repo
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while modifying the fragment.",
        )
