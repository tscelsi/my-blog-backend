import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from entities.fragments.file import File
from entities.fragments.rss import RSSFeed
from entities.fragments.text import RichText
from entities.user import User
from tags import Tag
from utils.logging_adapter import CustomLoggingAdapter
from utils.mixins import AuditMixin


class BaseMemoryError(Exception):
    """Base class for memory-related errors."""

    pass


class MemorySplitError(BaseMemoryError):
    """Error raised when a memory cannot be split."""

    pass


class MemoryNotFoundError(BaseMemoryError):
    pass


class MemoryAlreadyExistsError(BaseMemoryError):
    pass


class Memory(AuditMixin, BaseModel):
    """A memory. Made up of fragments."""

    title: str
    fragments: list[File | RichText | RSSFeed] = Field(
        default_factory=lambda: []
    )
    private: bool = Field(
        default=True, description="Whether this memory is private."
    )
    pinned: bool = Field(
        default=False, description="Whether this memory is pinned."
    )
    tags: set[Tag] = Field(
        default_factory=lambda: set(), description="Tags for this memory."
    )
    owner: UUID = Field()
    editors: set[UUID] = Field(
        default_factory=lambda: set(),
        description="Users allowed to edit this memory.",
    )
    readers: set[UUID] = Field(
        default_factory=lambda: set(),
        description="Users allowed to read this memory.",
    )

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._logger = CustomLoggingAdapter(
            logging.getLogger(__name__),
            {"ctx": f"memory:{self.id}"},
        )

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other: object):
        if not isinstance(other, Memory):
            return False
        return self.id == other.id

    def cedar_schema(self) -> dict[str, Any]:
        """Convert a Memory entity to a Cedar schema entity."""
        return {
            "uid": self.cedar_eid(),
            "attrs": {
                "editors": [
                    {"__entity": User(id=editor).cedar_eid()}
                    for editor in self.editors
                ],
                "readers": [
                    {"__entity": User(id=reader).cedar_eid()}
                    for reader in self.readers
                ],
                "owner": {"__entity": User(id=self.owner).cedar_eid()},
            },
            "parents": [],
        }

    def cedar_eid(self, as_str: bool = False) -> str | dict[str, str]:
        """Convert the Memory entity to a Cedar EID."""
        if as_str:
            return f'{__class__.__name__}::"{self.id}"'
        return {"id": str(self.id), "type": __class__.__name__}

    def get_fragment(self, fragment_id: UUID):
        for fragment in self.fragments:
            if fragment_id == fragment.id:
                return fragment
        raise ValueError(
            f"Fragment with ID {fragment_id} doesn't exist in memory {self.id}"
        )

    def list_fragments(self, fragment_ids: list[UUID]):
        """List fragments in memory."""
        return [f for f in self.fragments if f.id in fragment_ids]

    def merge(self, other: "Memory"):
        """Merge two memories."""
        self.fragments = self.fragments + other.fragments

    def split(self, fragment_ids: list[UUID]) -> "tuple[Memory, Memory]":
        """Split a memory.

        Takes some set of fragments and returns a new memory with those
        fragments."""
        fragments = self.list_fragments(fragment_ids)
        if not fragments:
            raise MemorySplitError(
                f"Fragments {fragment_ids} don't exist in memory {self.id}"
            )
        elif len(fragments) == len(self.fragments):
            raise MemorySplitError(
                f"Memory {self.id} would have no fragments left after split"
            )
        new_memory = Memory(
            title="_blank",
            owner=self.owner,
            created_by=self.owner,
            fragments=fragments,
        )
        self.fragments = [f for f in self.fragments if f not in fragments]
        return self, new_memory

    def forget_fragment(self, fragment_id: UUID):
        """Forget a fragment."""
        fragment = self.get_fragment(fragment_id)
        self.fragments.remove(fragment)
        self.updated_at = datetime.now(tz=timezone.utc)

    def update_fragment_ordering(self, fragment_ids: list[UUID]):
        """Update the ordering of fragments in memory."""
        self.fragments = [self.get_fragment(f) for f in fragment_ids]
        self.updated_at = datetime.now(tz=timezone.utc)

    def make_public(self):
        """Make a memory public."""
        self.private = False
        self.updated_at = datetime.now(tz=timezone.utc)

    def make_private(self):
        """This memory is private and a secret :)"""
        self.private = True
        self.updated_at = datetime.now(tz=timezone.utc)

    def pin(self):
        """Pin a memory."""
        self.pinned = True
        self.updated_at = datetime.now(tz=timezone.utc)

    def unpin(self):
        """Unpin a memory."""
        self.pinned = False
        self.updated_at = datetime.now(tz=timezone.utc)

    def set_tags(self, tags: set[Tag]):
        """Set new tags on the memory."""
        self.tags = tags
        self.updated_at = datetime.now(tz=timezone.utc)
