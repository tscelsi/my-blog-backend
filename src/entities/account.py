from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Account(BaseModel):
    """Account entity representing a user account."""

    id: UUID = Field(default_factory=uuid4)

    def cedar_schema(self) -> dict[str, Any]:
        """Convert the Account entity to a Cedar entity syntax.

        https://docs.cedarpolicy.com/auth/entities-syntax.html"""
        return {
            "uid": self.cedar_eid(),
            "attrs": {},
            "parents": [],
        }

    def cedar_eid(self, as_str: bool = False) -> str | dict[str, str]:
        """Convert the Account entity to a Cedar EID."""
        if as_str:
            return f'{__class__.__name__}::"{self.id}"'
        return {"id": str(self.id), "type": __class__.__name__}
