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
    Query,
    Request,
    UploadFile,
)
from pydantic import BaseModel

import services
from api.middleware.auth import require_auth_dep
from api.service_manager import ServiceManager
from fragments.base import FragmentType
from fragments.rss import RssFeedError
from fragments.text import Op
from memory_repository import (
    AbstractMemoryRepository,
    SupabaseMemoryRepository,
)
from utils.rss_parser import RssItem

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/fragment",
    dependencies=[Depends(require_auth_dep)],
)


def get_memory_repository_dep(request: Request) -> AbstractMemoryRepository:
    """Dependency to get the request-specific memory repository."""
    repo = SupabaseMemoryRepository(request.state.supabase_client)
    return repo


class AddFragmentResponse(BaseModel):
    fragment_id: UUID


@router.post("/file", status_code=201, response_model=AddFragmentResponse)
async def add_file_fragment_to_memory_endpoint(
    file: Annotated[UploadFile, File()],
    memory_id: Annotated[UUID, Form()],
    type: Annotated[FragmentType, Form()],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
) -> AddFragmentResponse:
    """Add a file Fragment to a Memory."""
    service_manager = ServiceManager.get()
    try:
        fragment_id = await services.add_file_fragment_to_memory(
            memory_id,
            type,
            file.filename or "_blank",
            file.file,
            service_manager.get_filesys(),
            repo,
            service_manager.background_tasks,
            service_manager.pub,
        )
        return AddFragmentResponse(fragment_id=fragment_id)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while adding a fragment to a memory.",
        )


@router.post("/rich-text", status_code=201, response_model=AddFragmentResponse)
async def add_rich_text_fragment_to_memory_endpoint(
    content: Annotated[list[Op], Body()],
    memory_id: Annotated[UUID, Body()],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
) -> AddFragmentResponse:
    """Add a rich text Fragment to a Memory."""
    try:
        fragment_id = await services.add_rich_text_fragment_to_memory(
            memory_id, content, repo
        )
        return AddFragmentResponse(fragment_id=fragment_id)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while adding a fragment to a memory.",
        )


@router.put("/rich-text", status_code=201, response_model=AddFragmentResponse)
async def modify_rich_text_fragment_endpoint(
    content: Annotated[list[Op], Body()],
    memory_id: Annotated[UUID, Body()],
    fragment_id: Annotated[UUID, Body()],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
) -> AddFragmentResponse:
    """Modify an existing rich text Fragment."""
    try:
        fragment_id = await services.modify_rich_text_fragment(
            memory_id, fragment_id, content, repo
        )
        return AddFragmentResponse(fragment_id=fragment_id)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while modifying the fragment.",
        )


@router.post("/rss", status_code=201, response_model=AddFragmentResponse)
async def add_rss_feed_fragment_to_memory_endpoint(
    urls: Annotated[list[str], Body()],
    memory_id: Annotated[UUID, Body()],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
) -> AddFragmentResponse:
    """Add an RSS feed Fragment to a Memory."""
    try:
        fragment_id = await services.add_rss_feed_to_memory(
            memory_id, urls, repo
        )
        return AddFragmentResponse(fragment_id=fragment_id)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while adding a fragment to a memory.",
        )


@router.get("/rss", status_code=201, response_model=list[RssItem])
async def get_rss_feed_channel_endpoint(
    memory_id: Annotated[UUID, Query()],
    fragment_id: Annotated[UUID, Query()],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
) -> list[RssItem]:
    """List the stories from an RSS feed Fragment."""
    try:
        items = await services.get_rss_feed_items(memory_id, fragment_id, repo)
    except RssFeedError as e:
        logger.exception(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving the RSS feed of a fragment.",  # noqa: E501
        )
    return items
