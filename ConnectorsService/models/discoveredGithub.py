from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DiscoveredGitHubFile:
    repository_id: int
    owner: str
    repository: str
    branch: str

    path: str
    blob_sha: str
    size_bytes: int | None
    source_url: str

    @property
    def external_id(self) -> str:
        return f"{self.repository_id}:{self.path}"

    @property
    def document_key(self) -> str:
        return f"github:{self.repository_id}:{self.path}"