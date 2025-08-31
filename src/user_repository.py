import abc
import logging
from uuid import UUID

from supabase import AsyncClient

from entities.user import UserNotFoundError

logger = logging.getLogger(__name__)


class AbstractUserRepository(abc.ABC):
    @abc.abstractmethod
    async def get_user_id_by_email(self, email: str) -> UUID:
        pass


class InMemoryUserRepository(AbstractUserRepository):
    def __init__(self, users: dict[str, UUID] = {}):
        self._users = users

    @property
    def size(self):
        return len(self._users)

    async def get_user_id_by_email(self, email: str) -> UUID:
        try:
            return self._users[email]
        except KeyError:
            raise UserNotFoundError(f"User with email {email} not found")


class SupabaseUserRepository(AbstractUserRepository):
    def __init__(self, client: AsyncClient):
        self.client = client
        self.table = self.client.schema("auth").table("users")

    async def get_user_id_by_email(self, email: str) -> UUID:
        try:
            result = await (
                self.table.select("id")
                .eq("email", email)
                .limit(1)
                .single()
                .execute()
            )
        except KeyError:
            raise UserNotFoundError(f"User with email {email} not found")
        if result.data:
            return UUID(result.data["id"])
        else:
            raise UserNotFoundError(f"User with email {email} not found")
