import abc
import logging
from typing import Iterable
from uuid import UUID

from supabase import AsyncClient

from entities.user import UserNotFoundError, UserWithEmail

logger = logging.getLogger(__name__)


class AbstractUserRepository(abc.ABC):
    @abc.abstractmethod
    async def get_user_id_by_email(self, email: str) -> UUID:
        pass

    @abc.abstractmethod
    async def get_user_emails_by_ids(
        self, ids: Iterable[UUID]
    ) -> list[UserWithEmail]:
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

    async def get_user_emails_by_ids(
        self, ids: Iterable[UUID]
    ) -> list[UserWithEmail]:
        id_to_email = {v: k for k, v in self._users.items()}
        return [
            UserWithEmail(id=id_, email=id_to_email[id_])
            for id_ in ids
            if id_ in id_to_email
        ]


class SupabaseUserRepository(AbstractUserRepository):
    def __init__(self, client: AsyncClient):
        self.client = client
        self.table = self.client.schema("public").table("users")

    async def get_user_id_by_email(self, email: str) -> UUID:
        try:
            result = await (
                self.table.select("id", "email")
                .eq("email", email)
                .single()
                .execute()
            )
        except KeyError:
            raise UserNotFoundError(f"User with email {email} not found")
        if result.data:
            return UUID(result.data["id"])
        else:
            raise UserNotFoundError(f"User with email {email} not found")

    async def get_user_emails_by_ids(
        self, ids: Iterable[UUID]
    ) -> list[UserWithEmail]:
        str_ids = [str(id_) for id_ in ids]
        result = await (
            self.table.select("id", "email").in_("id", str_ids).execute()
        )
        if not result.data:
            raise UserNotFoundError("No users found for the given IDs")
        return [
            UserWithEmail(id=UUID(item["id"]), email=item["email"])
            for item in result.data
        ]
