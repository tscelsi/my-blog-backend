from fragments.base import BaseFragment, FragmentType


class Text(BaseFragment):
    """A fragment of a memory. Text media, either plain text or a link."""

    content: str
    href: str | None = None

    @classmethod
    def from_content(cls, content: str):
        return cls(content=content, type=FragmentType.TEXT)

    def serialise(self) -> dict[str, str | int | None]:
        return {
            "id": str(self.id),
            "type": self.type.value,
            "content": self.content,
            "href": self.href,
        }
