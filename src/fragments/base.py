from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class FragmentType(Enum):
    """Fragment types."""

    FILE = "file"
    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"
    TEXT = "text"
    RICH_TEXT = "rich_text"


class BaseFragment(BaseModel):
    """Base class for fragments."""

    type: FragmentType
    id: UUID = Field(default_factory=uuid4)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other: object):
        if not isinstance(other, BaseFragment):
            return False
        return self.id == other.id

    def serialise(self) -> dict[str, Any]:
        """Serialise the fragment to a dictionary."""
        raise NotImplementedError(
            "Serialisation not implemented for the base fragment type. Must be implemented in subclasses."  # noqa
        )
