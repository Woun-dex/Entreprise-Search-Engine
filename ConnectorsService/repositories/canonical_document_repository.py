from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ConnectorsService.models.canonical_document import CanonicalDocumentModel


class CanonicalDocumentRepository:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_file_metadata_id(
        self,
        file_metadata_id: UUID,
    ) -> CanonicalDocumentModel | None:
        statement = select(CanonicalDocumentModel).where(
            CanonicalDocumentModel.file_metadata_id == file_metadata_id
        )

        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def add(
        self,
        canonical_document: CanonicalDocumentModel,
    ) -> None:
        self._session.add(canonical_document)
