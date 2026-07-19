from enum import StrEnum 

class ConnectorType(StrEnum):
    GITHUB = "GITHUB"
    CONFLUENCE = "CONFLUENCE"
    UPLOAD = "UPLOAD"


class ConnectorStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ERROR = "ERROR"

class FileStatus(StrEnum):
    DISCOVERED = "DISCOVERED"
    FETCHING = "FETCHING"
    FETCHED = "FETCHED"
    PARSED = "PARSED"
    CHUNKED = "CHUNKED"
    INDEXED = "INDEXED"
    FAILED = "FAILED"
    DELETED = "DELETED"

    