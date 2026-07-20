from datetime import datetime, timezone
from typing import Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class EventMetadata(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    source: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "1.0"
    correlation_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class EventEnvelope(BaseModel, Generic[T]):
    metadata: EventMetadata
    payload: T

    model_config = ConfigDict(from_attributes=True)
