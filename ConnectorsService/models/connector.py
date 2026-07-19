from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime , String , Text
from sqlalchemy.orm import Mapped , mapped_column , relationship

from ConnectorsService.db.base import Base , TimestampMixin , UUIDPrimaryKeyMixin


class ConnectorModel(
    UUIDPrimaryKeyMixin , TimestampMixin , Base
):
    __tablename__ = "connectors"

    connector_type: Mapped[str] = mapped_column(
        String(30), nullable=False ,)

    name: Mapped[str] = mapped_column(
        String(255), nullable=False ,)

    source_url: Mapped[str] = mapped_column(
        String(255), nullable=False ,)

    branch_name: Mapped[str] = mapped_column(
        String(255), nullable=False ,default="main" ,)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False ,default="ACTIVE" ,index=True ,
        )
    last_source_revision: Mapped[str] = mapped_column(
        String(255), nullable=True ,)
    last_successful_sync_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True ,)
    files: Mapped[list["FileMetadataModel"]] = relationship(
        back_populates="connector" ,cascade="all, delete-orphan" ,passive_deletes=True ,
        )