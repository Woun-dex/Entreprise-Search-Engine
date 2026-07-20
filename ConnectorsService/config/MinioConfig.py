from functools import lru_cache

from minio import Minio
from pydantic_settings import BaseSettings, SettingsConfigDict


class MinioSettings(BaseSettings):
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "miniopass"
    minio_secure: bool = False
    minio_raw_bucket: str = "raw-files"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_minio_settings() -> MinioSettings:
    return MinioSettings()


def get_minio_client(settings: MinioSettings) -> Minio:
    return Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )
