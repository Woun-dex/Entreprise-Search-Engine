from datetime import datetime
from typing import TYPE_CHECKING , Any
from uuid import UUID

from sqlalchemy import (
    BigInteger , DateTime , ForeignKey , String , Text , Index  ,UniqueConstraint
)

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped , mapped_column , relationship
from sqlalchemy.types import Uuid


from ConnectorsService.db.base import Base , TimestampMixin , UUIDPrimaryKeyMixin


if TYPE_CHECKING:
    from ConnectorsService.models.canonical_document import (
        CanonicalDocumentModel,
    )
    from ConnectorsService.models.connector import (
        ConnectorModel,
    )


class FileMetadataModel(
    UUIDPrimaryKeyMixin , TimestampMixin , Base
):
    __tablename__ = "file_metadata"

    __table_args__ = (
        UniqueConstraint("connector_id", "external_id", name="uq_file_metadata_connector_external_id" ),
    )

    connector_id: Mapped[UUID] = mapped_column(
        Uuid , ForeignKey("connectors.id", ondelete="CASCADE") ,nullable=False ,index=True ,
    )
    external_id: Mapped[str] = mapped_column(
        Text , nullable=False ,
    )
    file_path: Mapped[str] = mapped_column(
        Text , nullable=False ,
    )
    file_name: Mapped[str] = mapped_column(
        String(255) , nullable=False ,
    )
    source_version: Mapped[str] = mapped_column(
        String(255) , nullable=False ,
    )
    mime_type: Mapped[str] = mapped_column(
        String(100) , nullable=False ,
    )
    size_bytes: Mapped[int] = mapped_column(
        BigInteger , nullable=False ,
    )
    source_url: Mapped[str] = mapped_column(
        Text , nullable=False ,
    )
    raw_object_key: Mapped[str] = mapped_column(
        Text , nullable=False ,
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True) , nullable=False ,  
    )
    connector: Mapped["ConnectorModel"] = relationship(
        back_populates="files" ,
    )
    canonical_document: Mapped["CanonicalDocumentModel"] = relationship(
        back_populates="file_metadata", cascade="all, delete-orphan" , passive_deletes=True ,uselist=False ,
    )