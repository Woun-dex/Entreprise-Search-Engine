from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from opensearchpy import OpenSearch


class OpenSearchSettings(BaseSettings):
    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    opensearch_index: str = "enterprise-search-chunks"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_opensearch_settings() -> OpenSearchSettings:
    return OpenSearchSettings()


def get_opensearch_client(settings: OpenSearchSettings) -> OpenSearch:
    return OpenSearch(
        hosts=[{'host': settings.opensearch_host, 'port': settings.opensearch_port}],
        http_compress=True,
        use_ssl=False,
    )
