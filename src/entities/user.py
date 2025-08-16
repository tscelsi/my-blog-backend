from typing import Any
from uuid import UUID

from starlette.authentication import BaseUser

from .account import Account


class User(BaseUser):
    def __init__(self, id: UUID, account: UUID | None = None):
        self.id = id
        self.account = account

    def cedar_schema(self) -> dict[str, Any]:
        """Convert the User entity to a Cedar entity syntax.

        https://docs.cedarpolicy.com/auth/entities-syntax.html"""
        return {
            "uid": {"id": str(self.id), "type": __class__.__name__},
            "attrs": {
                "account": {"__entity": Account(id=self.account).cedar_eid()}
            }
            if self.account
            else {},
            "parents": [],
        }

    def cedar_eid(self, as_str: bool = False) -> str | dict[str, str]:
        """Convert the User entity to a Cedar EID."""
        if as_str:
            return f'{__class__.__name__}::"{self.id}"'
        return {"id": str(self.id), "type": __class__.__name__}

    @property
    def is_authenticated(self) -> bool:
        return True
