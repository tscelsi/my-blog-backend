from enum import Enum
from uuid import UUID

from pydantic import Field

from fragments.base import BaseFragment, FragmentType


class FileFragmentStatus(Enum):
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    ERROR = "error"


class File(BaseFragment):
    """A fragment of a memory that is a file. Could be an image, video, or
    audio."""

    name: str
    upload_progress: int = Field(default=0)
    status: FileFragmentStatus = Field(default=FileFragmentStatus.UPLOADING)
    url: str | None = Field(default=None)
    type: FragmentType = Field(default=FragmentType.FILE, frozen=True)

    def gen_key(self, user_id: UUID):
        return f"{user_id}/{self.name}"

    def __eq__(self, other: object):
        if not isinstance(other, File):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def serialise(self) -> dict[str, str | int | None]:
        return {
            "id": str(self.id),
            "name": self.name,
            "type": self.type.value,
            "upload_progress": self.upload_progress,
            "status": self.status.value,
            "url": self.url,
        }

    def set_upload_progress_error(self):
        self.status = FileFragmentStatus.ERROR

    def set_upload_succeeded(self):
        self.status = FileFragmentStatus.UPLOADED
        self.upload_progress = 100


class Audio(File):
    """A fragment of a memory that is an audio file."""

    type: FragmentType = Field(default=FragmentType.AUDIO, frozen=True)


class Image(File):
    """A fragment of a memory that is an image file."""

    type: FragmentType = Field(default=FragmentType.IMAGE, frozen=True)


class Video(File):
    """A fragment of a memory that is a video file."""

    type: FragmentType = Field(default=FragmentType.VIDEO, frozen=True)


class FileFragmentFactory:
    """Factory class for creating file fragments."""

    @staticmethod
    def create_file_fragment(name: str, type: FragmentType) -> File:
        if type == FragmentType.AUDIO:
            return Audio(name=name)
        elif type == FragmentType.IMAGE:
            return Image(name=name)
        elif type == FragmentType.VIDEO:
            return Video(name=name)
        else:
            return File(name=name)
