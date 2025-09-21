from typing import Any

from .base import BaseFragment, FragmentType

Op = dict[str, Any]


class Text(BaseFragment):
    """A fragment of a memory. Text media as a string."""

    content: str

    def serialise(
        self,
    ) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "type": self.type.value,
            "content": self.content,
        }

    @classmethod
    def from_content(cls, content: str):
        return cls(content=content, type=FragmentType.TEXT)


class RichText(BaseFragment):
    """A fragment of a memory. Text media, using the language of Quill JS for
    rich text support."""

    content: list[Op]

    def serialise(
        self,
    ) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "type": self.type.value,
            "content": tuple(self.content),
        }

    @classmethod
    def from_content(cls, content: list[Op]):
        return cls(content=content, type=FragmentType.RICH_TEXT)
