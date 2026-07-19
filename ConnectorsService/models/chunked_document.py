from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
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
    from ConnectorsService.models.canonical_document import (
        CanonicalDocumentModel,
    )


class DocumentChunkModel(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "document_chunks"

    __table_args__ = (
        UniqueConstraint(
            "canonical_document_id",
            "chunk_index",
            "chunking_version",
            name=(
                "uq_document_chunks_"
                "document_index_version"
            ),
        ),
        Index(
            "ix_document_chunks_document_status",
            "canonical_document_id",
            "index_status",
        ),
    )

    canonical_document_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey(
            "canonical_documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    chunk_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    heading_path: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    token_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    chunking_strategy: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    chunking_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    index_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
        index=True,
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    canonical_document: Mapped[
        "CanonicalDocumentModel"
    ] = relationship(
        back_populates="chunks"
    )