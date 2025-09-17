from datetime import datetime, timezone
from enum import Enum
from uuid import UUID

from pydantic import Field

from utils.file_storage.base_storage import AbstractFileStorage
from utils.file_storage.supabase_storage import PRESIGNED_URL_EXPIRY_SECONDS

from .base import BaseFragment, FragmentType


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
    url_last_generated: datetime | None = Field(default=None)
    type: FragmentType = Field(default=FragmentType.FILE, frozen=True)

    def gen_key(self, id: UUID):
        return f"{id}/{self.name}"

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

    async def check_presigned_url(
        self, id: UUID, ifilesys: AbstractFileStorage
    ):
        """Checks if the presigned URL to access the resource needs to be
        regenerated, and does so if necessary."""
        if self.url_last_generated is not None:
            delta = datetime.now(tz=timezone.utc) - self.url_last_generated
            if delta.total_seconds() < PRESIGNED_URL_EXPIRY_SECONDS:
                return  # don't regen if less than an hour old
        key = self.gen_key(id)
        old_last_generated = self.url_last_generated
        self.url_last_generated = datetime.now(tz=timezone.utc)
        try:
            self.url = await ifilesys.generate_presigned_url(key)
        except Exception:
            self.url = None
            self.url_last_generated = old_last_generated


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
