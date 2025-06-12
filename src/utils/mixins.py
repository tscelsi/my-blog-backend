from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AuditMixin(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
