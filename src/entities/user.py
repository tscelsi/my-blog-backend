from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from starlette.authentication import BaseUser


class BaseUserError(Exception):
    """Base class for user-related errors."""

    pass


class UserNotFoundError(BaseUserError):
    """Error raised when a user is not found."""

    pass


class Account(BaseModel):
    """Account entity representing a user account."""

    id: UUID = Field(default_factory=uuid4)

    def cedar_schema(self) -> dict[str, Any]:
        """Convert the Account entity to a Cedar entity syntax.

        https://docs.cedarpolicy.com/auth/entities-syntax.html"""
        return {
            "uid": self.cedar_eid_json(),
            "attrs": {},
            "parents": [],
        }

    def cedar_eid_str(self) -> str:
        """Convert the Account entity to a Cedar EID."""
        return f'{__class__.__name__}::"{self.id}"'

    def cedar_eid_json(self) -> dict[str, str]:
        return {"id": str(self.id), "type": __class__.__name__}


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
