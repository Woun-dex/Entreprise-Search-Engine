import uuid
import json
from typing import Any

from ConnectorsService.publisher.KafkaPublisher import KafkaPublisher
from ConnectorsService.schema.dead_letter import DeadLetterPayload
from ConnectorsService.schema.event_envelope import EventEnvelope, EventMetadata

def publish_to_dlq(
    publisher: KafkaPublisher,
    dlq_topic: str,
    worker_name: str,
    error_reason: str,
    original_message: bytes | str | Any,
    original_topic: str | None = None,
) -> None:
    """
    Publish a failed message to the Dead Letter Queue (DLQ).
    """
    # Attempt to parse original message if it's bytes or string to store as valid JSON in payload
    parsed_message = original_message
    if isinstance(original_message, (bytes, str)):
        try:
            parsed_message = json.loads(original_message)
        except (json.JSONDecodeError, TypeError):
            if isinstance(original_message, bytes):
                parsed_message = original_message.decode("utf-8", errors="replace")
    
    payload = DeadLetterPayload(
        original_topic=original_topic,
        original_message=parsed_message,
        error_reason=error_reason,
        worker_name=worker_name,
    )
    
    metadata = EventMetadata(
        event_type="dead_letter_event",
        source=worker_name,
    )
    
    event = EventEnvelope[DeadLetterPayload](
        metadata=metadata,
        payload=payload,
    )
    
    publisher.publish(
        topic=dlq_topic,
        key=str(uuid.uuid4()),
        event=event,
    )
    
    # Flush immediately to ensure the DLQ message is delivered
    publisher.flush(timeout_seconds=5.0)
