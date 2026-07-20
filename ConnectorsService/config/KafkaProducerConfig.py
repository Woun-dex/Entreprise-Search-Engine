from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer
from pydantic import BaseModel

from ConnectorsService.config.KafkaConfig import KafkaSettings
from ConnectorsService.config.KafkaClientConfig import common_kafka_config

def pydantic_serializer(obj: BaseModel, ctx) -> bytes | None:
    if obj is None:
        return None
    return obj.model_dump_json().encode("utf-8")


def create_producer(
    settings: KafkaSettings,
    client_name: str,
) -> SerializingProducer:
    config = common_kafka_config(settings)

    config.update(
        {
            "client.id": (
                f"{settings.kafka_client_id}-{client_name}"
            ),

            # Strong acknowledgement.
            "acks": "all",

            # Prevent duplicate records caused by producer retries.
            "enable.idempotence": True,

            # Retry temporary broker/network errors.
            "retries": 10,

            # Allow batching for better throughput.
            "linger.ms": 10,
            "batch.size": 65536,

            # Compress event payloads.
            "compression.type": "snappy",

            # Fail a delivery after this total period.
            "delivery.timeout.ms": 120000,

            # Time for a single broker request.
            "request.timeout.ms": 30000,
        }
    )

    config["key.serializer"] = StringSerializer("utf_8")
    config["value.serializer"] = pydantic_serializer

    return SerializingProducer(config)