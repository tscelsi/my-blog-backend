import logging
from uuid import UUID

from pydantic import BaseModel, Field
from starlette.authentication import BaseUser

from utils.mixins import AuditMixin

logger = logging.getLogger(__name__)


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

    @property
    def is_authenticated(self) -> bool:
        return True


class UserWithEmail(BaseModel):
    id: UUID
    email: str


class BaseAccountError(Exception):
    pass


class AccountNotFoundError(BaseAccountError):
    pass


class Account(AuditMixin, BaseModel):
    """Account entity representing a user account."""

    owner: UUID
    memories_pinned: set[UUID] = Field(default=set())

    def pin_memory(self, memory_id: UUID):
        self.memories_pinned.add(memory_id)

    def unpin_memory(self, memory_id: UUID):
        try:
            self.memories_pinned.remove(memory_id)
        except KeyError as e:
            logger.warning(e)
