from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ConnectorsService.models.connector import ConnectorModel
from ConnectorsService.models.enums import ConnectorStatus


class ConnectorRepository:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> Sequence[ConnectorModel]:
        statement = select(ConnectorModel)
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def get_active(self) -> Sequence[ConnectorModel]:
        statement = select(ConnectorModel).where(ConnectorModel.status == ConnectorStatus.ACTIVE)
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def get(self, connector_id: UUID) -> ConnectorModel | None:
        statement = select(ConnectorModel).where(ConnectorModel.id == connector_id)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def add(self, connector: ConnectorModel) -> None:
        self._session.add(connector)

    async def delete(self, connector_id: UUID) -> bool:
        connector = await self.get(connector_id)
        if connector:
            await self._session.delete(connector)
            return True
        return False
