from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_search.db.models.file_metadata import (
    FileMetadataModel,
)


class FileMetadataRepository:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_external_id(
        self,
        connector_id: UUID,
        external_id: str,
    ) -> FileMetadataModel | None:
        statement = select(FileMetadataModel).where(
            FileMetadataModel.connector_id == connector_id,
            FileMetadataModel.external_id == external_id,
        )

        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def add(
        self,
        file_metadata: FileMetadataModel,
    ) -> None:
        self._session.add(file_metadata)

    async def mark_fetched(
        self,
        file_metadata: FileMetadataModel,
        raw_object_key: str,
        fetched_at: datetime,
    ) -> None:
        file_metadata.raw_object_key = raw_object_key
        file_metadata.fetched_at = fetched_at
        file_metadata.status = "FETCHED"
        file_metadata.last_error = None

    async def mark_failed(
        self,
        file_metadata: FileMetadataModel,
        error: str,
    ) -> None:
        file_metadata.status = "FAILED"
        file_metadata.last_error = error