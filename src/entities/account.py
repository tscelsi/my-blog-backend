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
            "uid": self.cedar_eid_json(),
            "attrs": {},
            "parents": [],
        }

    def cedar_eid_str(self) -> str:
        """Convert the Account entity to a Cedar EID."""
        return f'{__class__.__name__}::"{self.id}"'

    def cedar_eid_json(self) -> dict[str, str]:
        return {"id": str(self.id), "type": __class__.__name__}
