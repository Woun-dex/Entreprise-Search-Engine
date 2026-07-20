import hashlib
import mimetypes
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from minio import Minio

from ConnectorsService.config.KafkaConfig import KafkaSettings
from ConnectorsService.db.session import AsyncSession
from ConnectorsService.models.file_metadata import FileMetadataModel
from ConnectorsService.publisher.KafkaPublisher import KafkaPublisher
from ConnectorsService.repositories.file_repository import FileMetadataRepository
from ConnectorsService.schema.event_envelope import EventEnvelope, EventMetadata
from ConnectorsService.schema.file_metadata import FileMetadata


SUPPORTED_EXTENSIONS = {
    ".md",
    ".markdown",
    ".txt",
    ".pdf",
    ".doc",
    ".docx",
}

IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    "target",
    "build",
    "dist",
    "vendor",
}


def compute_file_hash(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


class LocalDirectoryConnector:
    def __init__(
        self,
        connector_id: uuid.UUID,
        root_path: Path,
        session: AsyncSession,
        minio_client: Minio,
        minio_bucket: str,
        kafka_publisher: KafkaPublisher,
        kafka_settings: KafkaSettings,
    ) -> None:
        self.connector_id = connector_id
        self.root_path = root_path
        self.session = session
        self.repository = FileMetadataRepository(session)
        self.minio_client = minio_client
        self.minio_bucket = minio_bucket
        self.kafka_publisher = kafka_publisher
        self.kafka_settings = kafka_settings

    async def run(self) -> None:
        if not self.root_path.exists() or not self.root_path.is_dir():
            raise ValueError(f"Invalid root path: {self.root_path}")
            
        if not self.minio_client.bucket_exists(self.minio_bucket):
            self.minio_client.make_bucket(self.minio_bucket)

        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRECTORIES]

            for file_name in files:
                file_path = Path(root) / file_name
                if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                    continue
                    
                await self._process_file(file_path)

    async def _process_file(self, file_path: Path) -> None:
        try:
            relative_path = str(file_path.relative_to(self.root_path).as_posix())
            file_hash = compute_file_hash(file_path)
            
            existing_record = await self.repository.find_by_external_id(
                self.connector_id, relative_path
            )
            
            if existing_record and existing_record.source_version == file_hash:
                return
                
            object_key = f"{self.connector_id}/{relative_path}"
            
            self.minio_client.fput_object(
                bucket_name=self.minio_bucket,
                object_name=object_key,
                file_path=str(file_path),
            )
            
            now = datetime.now(timezone.utc)
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = "application/octet-stream"
                
            if existing_record:
                existing_record.source_version = file_hash
                existing_record.raw_object_key = object_key
                existing_record.fetched_at = now
                existing_record.size_bytes = file_path.stat().st_size
                existing_record.mime_type = mime_type
                record = existing_record
            else:
                record = FileMetadataModel(
                    connector_id=self.connector_id,
                    external_id=relative_path,
                    file_path=str(file_path),
                    file_name=file_path.name,
                    source_version=file_hash,
                    mime_type=mime_type,
                    size_bytes=file_path.stat().st_size,
                    source_url=f"local://{relative_path}",
                    raw_object_key=object_key,
                    fetched_at=now,
                )
                await self.repository.add(record)
                
            await self.session.flush()

            metadata_schema = FileMetadata.model_validate(record)
            
            envelope = EventEnvelope[FileMetadata](
                metadata=EventMetadata(
                    event_type="RawFileAvailable",
                    source="LocalDirectoryConnector",
                ),
                payload=metadata_schema,
            )
            
            self.kafka_publisher.publish(
                topic=self.kafka_settings.topic_raw_file_available,
                key=str(self.connector_id),
                event=envelope,
            )
            
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
