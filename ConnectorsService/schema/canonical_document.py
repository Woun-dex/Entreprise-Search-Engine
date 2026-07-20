from typing import Any, Optional
from uuid import UUID

from ConnectorsService.schema.base import BaseSchema, DBMixin


class CanonicalDocumentBase(BaseSchema):
    file_metadata_id: UUID
    document_key: str
    title: str
    content: str
    language: Optional[str] = None
    document_type: Optional[str] = None
    headings: list[str] = []
    document_metadata: dict[str, Any] = {}
    content_hash: str
    source_version: str


class CanonicalDocumentCreate(CanonicalDocumentBase):
    pass


class CanonicalDocumentUpdate(BaseSchema):
    title: Optional[str] = None
    content: Optional[str] = None
    language: Optional[str] = None
    document_type: Optional[str] = None
    headings: Optional[list[str]] = None
    document_metadata: Optional[dict[str, Any]] = None
    content_hash: Optional[str] = None
    source_version: Optional[str] = None


class CanonicalDocument(CanonicalDocumentBase, DBMixin):
    pass
