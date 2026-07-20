from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaSettings(BaseSettings):
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_client_id: str = "enterprise-search"

    kafka_security_protocol: str = "PLAINTEXT"
    kafka_sasl_mechanism: str | None = None
    kafka_sasl_username: str | None = None
    kafka_sasl_password: str | None = None

    topic_raw_file_available: str = "raw-file.available"
    topic_canonical_document_ready: str = "canonical-document.ready"
    topic_document_chunks_ready: str = "document-chunks.ready"
    topic_dead_letter: str = "pipeline.dead-letter"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_kafka_settings() -> KafkaSettings:
    return KafkaSettings()