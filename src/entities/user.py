from typing import Any
from uuid import UUID

from pydantic import BaseModel
from starlette.authentication import BaseUser

from entities.account import Account


class BaseUserError(Exception):
    """Base class for user-related errors."""

    pass


class UserNotFoundError(BaseUserError):
    """Error raised when a user is not found."""

    pass


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
                "account": {
                    "__entity": Account(id=self.account).cedar_eid_json()
                }
            }
            if self.account
            else {},
            "parents": [],
        }

    def cedar_eid_str(self) -> str:
        """Convert the User entity to a Cedar EID."""
        return f'{__class__.__name__}::"{self.id}"'

    def cedar_eid_json(self) -> dict[str, str]:
        return {"id": str(self.id), "type": __class__.__name__}

    @property
    def is_authenticated(self) -> bool:
        return True


class UserWithEmail(BaseModel):
    id: UUID
    email: str
