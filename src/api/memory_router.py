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
    Path,
    Request,
    UploadFile,
)
from pydantic import BaseModel

import services
from api.middleware.auth import require_auth_dep
from api.service_manager import ServiceManager
from fragments.base import FragmentType
from fragments.text import Op
from memory import BaseMemoryError, MemoryAlreadyExistsError
from memory_repository import (
    AbstractMemoryRepository,
    SupabaseMemoryRepository,
)
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


class CreateMemoryResponse(BaseModel):
    id: UUID


@router.post("", response_model=CreateMemoryResponse, status_code=201)
async def create_empty_memory(
    request: Request,
    memory_title: Annotated[str, Body()] = "blank_",
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
) -> CreateMemoryResponse:
    """Create an empty memory."""
    try:
        new_memory_id = await services.create_empty_memory(
            request.user.user_id, memory_title, repo
        )
    except MemoryAlreadyExistsError:
        raise HTTPException(
            status_code=400,
            detail="Memory already exists.",
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the memory.",
        )
    return CreateMemoryResponse(id=new_memory_id)


@router.post("/from-file", status_code=201, response_model=None)
async def create_memory_from_file(
    file: Annotated[UploadFile, File()],
    memory_title: Annotated[str, Form()],
    type: Annotated[FragmentType, Form()],
    request: Request,
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
) -> None:
    """Create a memory from a file."""
    service_manager = ServiceManager.get()
    logger.info("memory_title")
    logger.info(memory_title)
    try:
        await services.create_memory_from_file(
            request.user.user_id,
            memory_title,
            type,
            file.filename or "_blank",
            file.file,
            service_manager.get_filesys(),
            repo,
            service_manager.background_tasks,
            service_manager.pub,
        )
    except MemoryAlreadyExistsError as e:
        logger.error(e)
        raise HTTPException(
            status_code=400,
            detail="Memory already exists.",
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the memory.",
        )


@router.post("/from-rich-text", status_code=201, response_model=None)
async def create_memory_from_rich_text(
    content: Annotated[list[Op], Body()],
    memory_title: Annotated[str, Body()],
    request: Request,
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
) -> None:
    """Create a memory from rich text representation."""
    try:
        await services.create_memory_from_rich_text(
            request.user.user_id, memory_title, content, repo
        )
    except MemoryAlreadyExistsError as e:
        logger.error(e)
        raise HTTPException(
            status_code=400,
            detail="Memory already exists.",
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the memory.",
        )


class MemoryMergeRequest(BaseModel):
    """Merge Memory B into Memory A."""

    memory_a_id: UUID
    memory_b_id: UUID


@router.post("/merge", response_model=None, status_code=204)
async def merge_memories(
    body: MemoryMergeRequest,
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
):
    """Merge my memories."""
    try:
        await services.merge_memories(body.memory_a_id, body.memory_b_id, repo)
    except BaseMemoryError as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error merging memories: {e}")
        logger.exception(e)
        return HTTPException(status_code=500, detail="Error merging memories")


@router.post("/{memory_id}/update", response_model=None, status_code=204)
async def update_memory_endpoint(
    memory_id: Annotated[UUID, Path()],
    memory_title: Annotated[str, Body()],
    fragment_ids: Annotated[list[UUID], Body()],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
):
    """Update the title and ordering of fragments in a Memory."""
    try:
        await services.update_memory_title_and_ordering(
            memory_id, memory_title, fragment_ids, repo
        )
    except BaseMemoryError as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error merging memories: {e}")
        logger.exception(e)
        return HTTPException(status_code=500, detail="Error merging memories")


@router.post("/{memory_id}/split", response_model=None, status_code=204)
async def split_memory(
    memory_id: Annotated[UUID, Path()],
    fragment_ids: Annotated[list[UUID], Body(embed=True)],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
):
    """Split a memory in two."""
    try:
        await services.split_memory(memory_id, fragment_ids, repo)
    except BaseMemoryError as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error splitting memory: {e}")
        logger.exception(e)
        return HTTPException(status_code=500, detail="Error splitting memory")


@router.post("/{memory_id}/forget", status_code=204)
async def forget_memory(
    memory_id: Annotated[UUID, Path()],
    fragment_ids: Annotated[list[UUID] | None, Body(embed=True)] = None,
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
):
    """Forget a memory, or fragments of a memory."""
    service_manager = ServiceManager.get()
    try:
        if not fragment_ids:
            await services.forget_memory(
                memory_id,
                service_manager.get_filesys(),
                repo,
                service_manager.background_tasks,
                service_manager.pub,
            )
        else:
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


@router.put("/{memory_id}/set-private", status_code=204)
async def mark_memory_as_draft(
    memory_id: Annotated[UUID, Path()],
    private: Annotated[bool, Body(embed=True)],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
):
    """Mark a memory as a private or public."""
    try:
        if private:
            await services.make_memory_private(memory_id, repo)
        else:
            await services.make_memory_public(memory_id, repo)
    except BaseMemoryError as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error marking memory as draft: {e}")
        logger.exception(e)
        return HTTPException(
            status_code=500, detail="Error marking memory as draft"
        )


@router.put("/{memory_id}/set-pin", status_code=204)
async def pin_memory(
    memory_id: Annotated[UUID, Path()],
    pin: Annotated[bool, Body(embed=True)],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
):
    """Pin or unpin a memory."""
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
    memory_id: Annotated[UUID, Path()],
    tags: Annotated[set[Tag], Body(embed=True)],
    repo: AbstractMemoryRepository = Depends(get_memory_repository_dep),
):
    """Tag a memory."""
    try:
        await services.update_tags(memory_id, tags, repo)
    except BaseMemoryError as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error tagging memory: {e}")
        logger.exception(e)
        return HTTPException(status_code=500, detail="Error tagging memory")
