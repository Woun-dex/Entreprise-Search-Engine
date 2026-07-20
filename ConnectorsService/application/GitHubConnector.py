import io
import mimetypes
from datetime import datetime, timezone

import httpx
from minio import Minio

from ConnectorsService.config.KafkaConfig import KafkaSettings
from ConnectorsService.db.session import AsyncSession
from ConnectorsService.models.connector import ConnectorModel
from ConnectorsService.models.file_metadata import FileMetadataModel
from ConnectorsService.publisher.KafkaPublisher import KafkaPublisher
from ConnectorsService.repositories.file_repository import FileMetadataRepository
from ConnectorsService.schema.event_envelope import EventEnvelope, EventMetadata
from ConnectorsService.schema.file_metadata import FileMetadata

SUPPORTED_EXTENSIONS = {".md", ".markdown", ".txt"}


class GitHubConnector:
    def __init__(
        self,
        connector: ConnectorModel,
        session: AsyncSession,
        minio_client: Minio,
        minio_bucket: str,
        kafka_publisher: KafkaPublisher,
        kafka_settings: KafkaSettings,
    ) -> None:
        self.connector = connector
        self.session = session
        self.repository = FileMetadataRepository(session)
        self.minio_client = minio_client
        self.minio_bucket = minio_bucket
        self.kafka_publisher = kafka_publisher
        self.kafka_settings = kafka_settings

    async def run(self) -> None:
        parts = self.connector.source_url.rstrip("/").split("/")
        if len(parts) < 5:
            print(f"Invalid github URL: {self.connector.source_url}")
            return
            
        owner = parts[3]
        repo = parts[4]
        
        branch = self.connector.branch_name or "main"

        async with httpx.AsyncClient() as client:
            url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
            response = await client.get(url)
            if response.status_code != 200:
                print(f"Failed to fetch repo {owner}/{repo}: {response.status_code}")
                return
                
            tree_data = response.json()
            if tree_data.get("truncated"):
                print("Warning: GitHub tree truncated.")

            for item in tree_data.get("tree", []):
                if item["type"] != "blob":
                    continue
                    
                path = item["path"]
                if not any(path.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                    continue
                    
                file_hash = item["sha"]
                size_bytes = item.get("size", 0)
                
                await self._process_file(owner, repo, branch, path, file_hash, size_bytes, client)
                
    async def _process_file(self, owner: str, repo: str, branch: str, path: str, file_hash: str, size_bytes: int, client: httpx.AsyncClient) -> None:
        try:
            existing_record = await self.repository.find_by_external_id(
                self.connector.id, path
            )
            
            if existing_record and existing_record.source_version == file_hash:
                return
                
            download_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
            response = await client.get(download_url)
            if response.status_code != 200:
                print(f"Failed to download {path}")
                return
                
            content = response.content
            
            object_key = f"{self.connector.id}/{path}"
            self.minio_client.put_object(
                bucket_name=self.minio_bucket,
                object_name=object_key,
                data=io.BytesIO(content),
                length=len(content),
            )
            
            now = datetime.now(timezone.utc)
            mime_type, _ = mimetypes.guess_type(path)
            if not mime_type:
                mime_type = "text/plain"
                
            if existing_record:
                existing_record.source_version = file_hash
                existing_record.raw_object_key = object_key
                existing_record.fetched_at = now
                existing_record.size_bytes = size_bytes
                existing_record.mime_type = mime_type
                record = existing_record
            else:
                record = FileMetadataModel(
                    connector_id=self.connector.id,
                    external_id=path,
                    file_path=path,
                    file_name=path.split("/")[-1],
                    source_version=file_hash,
                    mime_type=mime_type,
                    size_bytes=size_bytes,
                    source_url=download_url,
                    raw_object_key=object_key,
                    fetched_at=now,
                )
                await self.repository.add(record)
                
            await self.session.flush()

            metadata_schema = FileMetadata.model_validate(record)
            
            envelope = EventEnvelope[FileMetadata](
                metadata=EventMetadata(
                    event_type="RawFileAvailable",
                    source="GitHubConnector",
                ),
                payload=metadata_schema,
            )
            
            self.kafka_publisher.publish(
                topic=self.kafka_settings.topic_raw_file_available,
                key=str(self.connector.id),
                event=envelope,
            )
            
        except Exception as e:
            print(f"Error processing GitHub file {path}: {e}")
