from typing import Optional
from uuid import UUID

from ConnectorsService.schema.base import BaseSchema, DBMixin


class DocumentChunkBase(BaseSchema):
    canonical_document_id: UUID
    chunk_key: str
    chunk_index: int
    title: str
    heading_path: list[str] = []
    content: str
    content_hash: str
    token_count: Optional[int] = None
    chunking_strategy: str
    chunking_version: str
    index_status: str = "PENDING"
    last_error: Optional[str] = None


class DocumentChunkCreate(DocumentChunkBase):
    pass


class DocumentChunkUpdate(BaseSchema):
    index_status: Optional[str] = None
    last_error: Optional[str] = None


class DocumentChunk(DocumentChunkBase, DBMixin):
    pass
