from confluent_kafka.admin import (
    AdminClient,
    NewTopic,
)

from ConnectorsService.config.KafkaConfig import KafkaSettings
from ConnectorsService.config.KafkaClientConfig import common_kafka_config


def create_topics(settings: KafkaSettings) -> None:
    admin = AdminClient(common_kafka_config(settings))

    topic_definitions = [

        NewTopic(
            settings.topic_raw_file_available,
            num_partitions=3,
            replication_factor=1,
            config={
                "cleanup.policy": "delete",
                "retention.ms": str(7 * 24 * 60 * 60 * 1000),
            },
        ),

        NewTopic(
            settings.topic_dead_letter,
            num_partitions=1,
            replication_factor=1,
            config={
                "cleanup.policy": "delete",
                "retention.ms": str(
                    30 * 24 * 60 * 60 * 1000
                ),
            },
        ),
    ]

    futures = admin.create_topics(topic_definitions)

    for topic, future in futures.items():
        try:
            future.result()
            print(f"Created topic: {topic}")
        except Exception as error:
            message = str(error)

            if "TOPIC_ALREADY_EXISTS" in message:
                print(f"Topic already exists: {topic}")
            else:
                raise