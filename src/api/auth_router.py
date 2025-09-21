from fastapi import APIRouter, Depends, Request

from account_management.account_repository import (
    AbstractAccountRepository,
    SupabaseAccountRepository,
)
from api.middleware.auth import require_auth_dep
from entities.user import Account


def get_account_repository_dep(request: Request) -> AbstractAccountRepository:
    """Dependency to get the request-specific memory repository."""
    repo = SupabaseAccountRepository(request.state.supabase_client)
    return repo


router = APIRouter(
    prefix="/auth",
    dependencies=[Depends(require_auth_dep)],
)


@router.get("/account", response_model=Account)
async def get_account(
    request: Request,
    repo: AbstractAccountRepository = Depends(get_account_repository_dep),
):
    """Get the account of the authenticated user."""
    account = await repo.get_by_user_id(request.user.id)
    return account
