from confluent_kafka import DeserializingConsumer
from confluent_kafka.serialization import StringDeserializer

from ConnectorsService.config.KafkaConfig import KafkaSettings
from ConnectorsService.config.KafkaClientConfig import common_kafka_config

def create_consumer(
    settings: KafkaSettings,
    *,
    group_id: str,
    client_name: str,
) -> DeserializingConsumer:
    config = common_kafka_config(settings)

    config.update(
        {
            "client.id": (
                f"{settings.kafka_client_id}-{client_name}"
            ),

            "group.id": group_id,

            # Do not commit before successful processing.
            "enable.auto.commit": False,

            # Do not mark records consumed automatically.
            "enable.auto.offset.store": False,

            # New groups begin with existing events.
            "auto.offset.reset": "earliest",

            # Parsing can be slow. Increase this if necessary,
            # but keep processing bounded.
            "max.poll.interval.ms": 300000,

            "session.timeout.ms": 45000,

            # Avoid retrieving huge batches into one worker.
            "max.poll.records": 20,
        }
    )

    config["key.deserializer"] = StringDeserializer("utf_8")
    
    # Values will be received as raw bytes/strings. 
    # The application layer will manually deserialize using the appropriate Pydantic model 
    # depending on the topic. So we do not set value.deserializer here, allowing the 
    # consumer to return the raw value, or we could set a generic bytes deserializer.

    return DeserializingConsumer(config)