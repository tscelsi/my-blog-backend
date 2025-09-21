import abc
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ResourceType(str, Enum):
    MEMORY = "Memory"
    ACCOUNT = "Account"
    USER = "User"


class AbstractCedarResource(abc.ABC):
    @abc.abstractmethod
    def cedar_schema(self) -> dict[str, Any]:
        pass

    @abc.abstractmethod
    def cedar_eid_str(self) -> str:
        pass

    @abc.abstractmethod
    def cedar_eid_json(self) -> dict[str, str]:
        pass


class CedarAccount(AbstractCedarResource, BaseModel):
    id: UUID
    owner: UUID

    def cedar_schema(self) -> dict[str, Any]:
        """Cedar entity syntax Account.

        https://docs.cedarpolicy.com/auth/entities-syntax.html"""
        return {
            "uid": self.cedar_eid_json(),
            "attrs": {
                "owner": {
                    "__entity": {
                        "id": str(self.owner),
                        "type": ResourceType.USER.value,
                    }
                }
            },
            "parents": [],
        }

    def cedar_eid_str(self) -> str:
        """Convert the User entity to a Cedar EID."""
        return f'{ResourceType.ACCOUNT.value}::"{self.id}"'

    def cedar_eid_json(self) -> dict[str, str]:
        return {"id": str(self.id), "type": ResourceType.ACCOUNT.value}


class CedarUser(AbstractCedarResource, BaseModel):
    id: UUID
    account: UUID | None = None

    @classmethod
    def from_user(cls, user: object) -> "CedarUser":
        if not hasattr(user, "id") or not hasattr(user, "account"):
            raise ValueError(
                "User object must have 'id' and 'account' attributes"
            )
        return cls(id=user.id, account=user.account)  # type: ignore[attr-defined]  # noqa: E501

    def cedar_schema(self) -> dict[str, Any]:
        """Convert the User entity to a Cedar entity syntax.

        https://docs.cedarpolicy.com/auth/entities-syntax.html"""
        account = (
            {
                "account": {
                    "__entity": {
                        "id": str(self.account),
                        "owner": str(self.id),
                        "type": ResourceType.ACCOUNT.value,
                    }
                }
            }
            if self.account
            else {}
        )
        return {
            "uid": self.cedar_eid_json(),
            "attrs": {**account},
            "parents": [],
        }

    def cedar_eid_str(self) -> str:
        """Convert the User entity to a Cedar EID."""
        return f'{ResourceType.USER.value}::"{self.id}"'

    def cedar_eid_json(self) -> dict[str, str]:
        return {"id": str(self.id), "type": ResourceType.USER.value}


class CedarMemory(AbstractCedarResource, BaseModel):
    id: UUID
    owner: UUID | None = None
    editors: set[UUID] | None = None
    readers: set[UUID] | None = None
    private: bool | None = None

    def cedar_schema(self) -> dict[str, Any]:
        """Convert a resource to a Cedar schema entity."""
        editors = (
            {
                "editors": [
                    {
                        "__entity": {
                            "id": str(editor),
                            "type": ResourceType.USER.value,
                        }
                    }
                    for editor in self.editors
                ]
            }
            if self.editors is not None
            else {}
        )
        readers = (
            {
                "readers": [
                    {
                        "__entity": {
                            "id": str(reader),
                            "type": ResourceType.USER.value,
                        }
                    }
                    for reader in self.readers
                ]
            }
            if self.readers is not None
            else {}
        )
        owner = (
            {
                "owner": {
                    "__entity": {
                        "id": str(self.owner),
                        "type": ResourceType.USER.value,
                    }
                }
            }
            if self.owner is not None
            else {}
        )
        private = {"private": self.private} if self.private is not None else {}
        return {
            "uid": self.cedar_eid_json(),
            "attrs": {**editors, **readers, **owner, **private},
            "parents": [],
        }

    def cedar_eid_str(self) -> str:
        """Convert the User entity to a Cedar EID."""
        return f'{ResourceType.MEMORY.value}::"{self.id}"'

    def cedar_eid_json(self) -> dict[str, str]:
        return {"id": str(self.id), "type": ResourceType.MEMORY.value}
