import json
from typing import Any
from collections.abc import Callable

from confluent_kafka import KafkaError, Message, SerializingProducer


class KafkaPublisher:

    def __init__(self, producer: SerializingProducer) -> None:
        self._producer = producer

    def publish(
        self,
        *,
        topic: str,
        key: str,
        event: Any, # EventEnvelope
    ) -> None:
        self._producer.produce(
            topic=topic,
            key=key,
            value=event,
            headers={
                "event-type": event.metadata.event_type.encode("utf-8"),
                "event-version": str(
                    event.metadata.version
                ).encode("utf-8"),
                "correlation-id": str(
                    event.metadata.correlation_id or ""
                ).encode("utf-8"),
            },
            on_delivery=self._on_delivery,
        )

        # Serve delivery callbacks and free producer queue space.
        self._producer.poll(0)

    def flush(self, timeout_seconds: float = 10.0) -> None:
        remaining = self._producer.flush(timeout_seconds)

        if remaining > 0:
            raise RuntimeError(
                f"{remaining} Kafka events were not delivered"
            )

    @staticmethod
    def _on_delivery(
        error: KafkaError | None,
        message: Message,
    ) -> None:
        if error is not None:
            raise RuntimeError(
                f"Kafka delivery failed: {error}"
            )