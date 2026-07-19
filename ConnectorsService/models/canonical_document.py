from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from ConnectorsService.db.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from ConnectorsService.models.chunked_document import (
        DocumentChunkModel,
    )
    from ConnectorsService.models.file_metadata import (
        FileMetadataModel,
    )


class CanonicalDocumentModel(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "canonical_documents"

    file_metadata_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey(
            "file_metadata.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )

    document_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )

    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    language: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    document_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    headings: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    document_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )


    source_version: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    file_metadata: Mapped["FileMetadataModel"] = relationship(
        back_populates="canonical_document"
    )

    chunks: Mapped[list["DocumentChunkModel"]] = relationship(
        back_populates="canonical_document",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="DocumentChunkModel.chunk_index",
    )
