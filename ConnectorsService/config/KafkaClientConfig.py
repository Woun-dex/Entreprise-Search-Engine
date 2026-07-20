from typing import Any

from ConnectorsService.config.KafkaConfig import KafkaSettings


def common_kafka_config(
    settings: KafkaSettings,
) -> dict[str, Any]:
    config: dict[str, Any] = {
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        "client.id": settings.kafka_client_id,
        "security.protocol": settings.kafka_security_protocol,
    }

    if settings.kafka_sasl_mechanism:
        config["sasl.mechanism"] = settings.kafka_sasl_mechanism

    if settings.kafka_sasl_username:
        config["sasl.username"] = settings.kafka_sasl_username

    if settings.kafka_sasl_password:
        config["sasl.password"] = settings.kafka_sasl_password

    return config