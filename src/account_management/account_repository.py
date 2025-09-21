import abc
import logging
from datetime import datetime, timezone
from uuid import UUID

from supabase import AsyncClient

from entities.user import Account, AccountNotFoundError

logger = logging.getLogger(__name__)


class AbstractAccountRepository(abc.ABC):
    @abc.abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Account:
        pass

    @abc.abstractmethod
    async def update(self, account: Account) -> None:
        pass


class InMemoryAccountRepository(AbstractAccountRepository):
    def __init__(self, accounts: list[Account] = []):
        self._accounts = accounts

    @property
    def size(self):
        return len(self._accounts)

    async def get_by_user_id(self, user_id: UUID) -> Account:
        result = [acc for acc in self._accounts if user_id == acc.owner]
        if not result:
            raise AccountNotFoundError(
                f"Account with owner {user_id} not found"
            )
        return result[0]

    async def update(self, account: Account) -> None:
        await self.get_by_user_id(account.owner)


class SupabaseAccountRepository(AbstractAccountRepository):
    def __init__(self, client: AsyncClient):
        self.client = client
        self.table = self.client.table("accounts")

    async def get_by_user_id(self, user_id: UUID) -> Account:
        res = await self.table.select("*").eq("owner", str(user_id)).execute()
        if hasattr(res, "data") and res.data:
            data = res.data[0]
            return Account(
                owner=data["owner"],
                id=data["id"],
                memories_pinned=data["memories_pinned"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                created_by=data["created_by"],
                updated_by=data["updated_by"],
            )
        raise AccountNotFoundError(f"Account with owner {user_id} not found")

    async def update(self, account: Account) -> None:
        await (
            self.table.update(  # type: ignore
                {
                    "memories_pinned": [
                        str(id_) for id_ in account.memories_pinned
                    ],
                    "updated_at": datetime.now(tz=timezone.utc).isoformat(),
                }
            )
            .eq("id", str(account.id))
            .execute()
        )
