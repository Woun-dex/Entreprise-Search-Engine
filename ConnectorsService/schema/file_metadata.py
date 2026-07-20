from datetime import datetime
from typing import Optional
from uuid import UUID

from ConnectorsService.schema.base import BaseSchema, DBMixin


class FileMetadataBase(BaseSchema):
    connector_id: UUID
    external_id: str
    file_path: str
    file_name: str
    source_version: str
    mime_type: str
    size_bytes: int
    source_url: str
    raw_object_key: str
    fetched_at: datetime


class FileMetadataCreate(FileMetadataBase):
    pass


class FileMetadataUpdate(BaseSchema):
    external_id: Optional[str] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    source_version: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    source_url: Optional[str] = None
    raw_object_key: Optional[str] = None
    fetched_at: Optional[datetime] = None


class FileMetadata(FileMetadataBase, DBMixin):
    pass
