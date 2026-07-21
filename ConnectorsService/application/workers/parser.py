import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from opensearchpy import OpenSearch
from ConnectorsService.config.KafkaConfig import get_kafka_settings
from ConnectorsService.config.KafkaConsumerConfig import create_consumer
from ConnectorsService.config.MinioConfig import get_minio_settings, get_minio_client
from ConnectorsService.config.OpenSearchConfig import get_opensearch_settings, get_opensearch_client
from ConnectorsService.db.session import AsyncSessionFactory
from ConnectorsService.models.canonical_document import CanonicalDocumentModel
from ConnectorsService.models.chunked_document import DocumentChunkModel
from ConnectorsService.repositories.canonical_document_repository import CanonicalDocumentRepository
from ConnectorsService.schema.event_envelope import EventEnvelope
from ConnectorsService.schema.file_metadata import FileMetadata
from ConnectorsService.config.KafkaProducerConfig import create_producer
from ConnectorsService.publisher.KafkaPublisher import KafkaPublisher
from ConnectorsService.publisher.dlq_publisher import publish_to_dlq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("parser_worker")

def parse_markdown_or_text(content: str) -> tuple[str, list[str], str]:
    """Simple parser that extracts title, headings, and raw content."""
    lines = content.splitlines()
    title = "Untitled Document"
    headings = []
    
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()
        
    for line in lines:
        if line.startswith("#"):
            headings.append(line.lstrip("#").strip())
            
    return title, headings, content

def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        if end < text_len:
            nice_break = text.rfind("\n", start, end)
            if nice_break != -1 and nice_break > start + chunk_size // 2:
                end = nice_break + 1
            else:
                nice_break = text.rfind(" ", start, end)
                if nice_break != -1 and nice_break > start + chunk_size // 2:
                    end = nice_break + 1
                    
        chunks.append(text[start:end])
        start = end - overlap
        if start < 0 or start >= end:
            start = end 
            
    return chunks

async def process_message(
    msg_value: bytes,
    session,
    minio_client,
    os_client: OpenSearch,
    minio_settings,
    os_settings,
):
    data = json.loads(msg_value)
    envelope = EventEnvelope[FileMetadata].model_validate(data)

    metadata = envelope.payload
    
    logger.info(f"Processing raw file: {metadata.file_path}")
    
    tmp_path = Path("/tmp") / metadata.raw_object_key.split("/")[-1]
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    
    minio_client.fget_object(
        bucket_name=minio_settings.minio_raw_bucket,
        object_name=metadata.raw_object_key,
        file_path=str(tmp_path),
    )
    
    with open(tmp_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    title, headings, clean_content = parse_markdown_or_text(content)
    content_hash = compute_hash(clean_content)
    
    repo = CanonicalDocumentRepository(session)
    existing_doc = await repo.find_by_file_metadata_id(metadata.id)
    
    now = datetime.now(timezone.utc)
    
    if existing_doc:
        if existing_doc.content_hash == content_hash:
            logger.info("Document unchanged, skipping.")
            tmp_path.unlink(missing_ok=True)
            return
            
        existing_doc.title = title
        existing_doc.content = clean_content
        existing_doc.headings = headings
        existing_doc.content_hash = content_hash
        existing_doc.source_version = metadata.source_version
        record = existing_doc
    else:
        record = CanonicalDocumentModel(
            file_metadata_id=metadata.id,
            document_key=metadata.raw_object_key,
            title=title,
            content=clean_content,
            language="en",
            document_type="markdown",
            headings=headings,
            document_metadata={},
            content_hash=content_hash,
            source_version=metadata.source_version,
        )
        await repo.add(record)
        
    await session.flush()
    
    if not os_client.indices.exists(index=os_settings.opensearch_index):
        os_client.indices.create(index=os_settings.opensearch_index)
        
    text_chunks = chunk_text(clean_content)
    
    for i, text in enumerate(text_chunks):
        chunk_hash = compute_hash(text)
        chunk_key = f"{record.id}-chunk-{i}"
        
        chunk_record = DocumentChunkModel(
            canonical_document_id=record.id,
            chunk_key=chunk_key,
            chunk_index=i,
            title=title,
            heading_path=headings,
            content=text,
            content_hash=chunk_hash,
            chunking_strategy="sliding_window_1000_200",
            chunking_version="1.0",
            index_status="INDEXED"
        )
        session.add(chunk_record)
        
        os_doc = {
            "chunk_key": chunk_key,
            "canonical_document_id": str(record.id),
            "connector_id": str(metadata.connector_id),
            "title": title,
            "headings": headings,
            "content": text,
            "source_url": metadata.source_url,
            "chunk_index": i,
            "timestamp": now.isoformat()
        }
        
        try:
            os_client.index(
                index=os_settings.opensearch_index,
                body=os_doc,
                id=chunk_key,
                refresh=True
            )
        except Exception as e:
            logger.error(f"Failed to index chunk {chunk_key}: {e}")
            chunk_record.index_status = "FAILED"
            chunk_record.last_error = str(e)
            
    await session.flush()
    logger.info(f"Successfully processed and indexed {len(text_chunks)} chunks for {metadata.file_path}")
    
    tmp_path.unlink(missing_ok=True)

async def main():
    kafka_settings = get_kafka_settings()
    minio_settings = get_minio_settings()
    os_settings = get_opensearch_settings()
    
    consumer = create_consumer(
        kafka_settings,
        group_id="parser-workers",
        client_name="parser-1"
    )
    
    minio_client = get_minio_client(minio_settings)
    os_client = get_opensearch_client(os_settings)
    
    producer = create_producer(kafka_settings, client_name="parser-dlq-producer")
    dlq_publisher = KafkaPublisher(producer)
    
    consumer.subscribe([kafka_settings.topic_raw_file_available])
    logger.info("Consolidated parser/chunker worker started. Listening for RawFileAvailable events...")
    
    try:
        while True:
            msg = await asyncio.to_thread(consumer.poll, 1.0)
            
            if msg is None:
                continue
            if msg.error():
                logger.error(f"Consumer error: {msg.error()}")
                continue
                
            try:
                async with AsyncSessionFactory() as session:
                    await process_message(
                        msg.value(),
                        session,
                        minio_client,
                        os_client,
                        minio_settings,
                        os_settings
                    )
                    await session.commit()
            except Exception as e:
                logger.error(f"Error processing message: {e}. Publishing to DLQ.")
                publish_to_dlq(
                    publisher=dlq_publisher,
                    dlq_topic=kafka_settings.topic_dead_letter,
                    worker_name="parser-worker",
                    error_reason=str(e),
                    original_message=msg.value(),
                    original_topic=msg.topic()
                )
                
            consumer.commit(message=msg)
            
    except KeyboardInterrupt:
        logger.info("Shutting down worker...")
    finally:
        consumer.close()

if __name__ == "__main__":
    asyncio.run(main())
