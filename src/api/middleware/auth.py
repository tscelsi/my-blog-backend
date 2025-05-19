import logging
from uuid import UUID

from fastapi import HTTPException, Request
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    BaseUser,
)
from starlette.requests import HTTPConnection

from api.service_manager import ServiceManager

logger = logging.getLogger(__name__)


class User(BaseUser):
    def __init__(self, user_id: str):
        self.user_id = UUID(user_id)

    @property
    def is_authenticated(self) -> bool:
        return True


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
        return AuthCredentials(["authenticated"]), User(user_id=res.user.id)


async def require_auth_dep(
    request: Request,
) -> None:
    """Dependency to require authentication."""
    if not request.user.is_authenticated:
        raise HTTPException(status_code=401, detail="Not authenticated")
