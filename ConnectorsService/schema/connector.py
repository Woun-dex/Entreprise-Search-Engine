from datetime import datetime
from typing import Optional

from ConnectorsService.models.enums import ConnectorStatus, ConnectorType
from ConnectorsService.schema.base import BaseSchema, DBMixin


class ConnectorBase(BaseSchema):
    connector_type: ConnectorType | str
    name: str
    source_url: str
    branch_name: str = "main"
    status: ConnectorStatus | str = ConnectorStatus.ACTIVE
    last_source_revision: Optional[str] = None
    last_successful_sync_at: Optional[datetime] = None


class ConnectorCreate(ConnectorBase):
    pass


class ConnectorUpdate(BaseSchema):
    connector_type: Optional[ConnectorType | str] = None
    name: Optional[str] = None
    source_url: Optional[str] = None
    branch_name: Optional[str] = None
    status: Optional[ConnectorStatus | str] = None
    last_source_revision: Optional[str] = None
    last_successful_sync_at: Optional[datetime] = None


class Connector(ConnectorBase, DBMixin):
    pass
