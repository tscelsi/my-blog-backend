import logging
from uuid import UUID

from fastapi import HTTPException, Request
from starlette.authentication import AuthCredentials, AuthenticationBackend
from starlette.requests import HTTPConnection

from api.service_manager import ServiceManager
from entities.user import User

logger = logging.getLogger(__name__)


class AuthBackend(AuthenticationBackend):
    async def authenticate(self, conn: HTTPConnection):
        sm = ServiceManager.get()
        if "Authorization" not in conn.headers:
            return

        auth = conn.headers.get("Authorization")
        # check if auth is bearer token
        if auth is None or not auth.startswith("Bearer "):
            return
        auth = auth[7:]
        try:
            res = await sm.get_supabase_client().auth.get_user(auth)
        except Exception as e:
            logger.exception(e)
            return
        if res is None:
            return
        try:
            account = (
                await sm.get_supabase_client()
                .table("accounts")
                .select("id")
                .eq("owner", res.user.id)
                .limit(1)
                .single()
                .execute()
            )
        except Exception as e:
            logger.exception(e)
            return
        if not account.data or not account.data.get("id"):
            # with no account, we cannot authorise the user and should fail
            return None
        return AuthCredentials(["authenticated"]), User(
            id=UUID(res.user.id), account=UUID(account.data["id"])
        )


async def require_auth_dep(
    request: Request,
) -> None:
    """Dependency to require authentication."""
    if not request.user.is_authenticated:
        raise HTTPException(status_code=401, detail="Not authenticated")
