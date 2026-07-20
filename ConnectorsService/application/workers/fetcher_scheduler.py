import asyncio

from ConnectorsService.application.Connectors import LocalDirectoryConnector
from ConnectorsService.application.GitHubConnector import GitHubConnector
from ConnectorsService.config.KafkaConfig import get_kafka_settings
from ConnectorsService.config.KafkaProducerConfig import create_producer
from ConnectorsService.config.MinioConfig import get_minio_settings, get_minio_client
from ConnectorsService.db.session import AsyncSessionFactory
from ConnectorsService.models.enums import ConnectorType
from ConnectorsService.publisher.KafkaPublisher import KafkaPublisher
from ConnectorsService.repositories.connector_repository import ConnectorRepository


async def main() -> None:
    kafka_settings = get_kafka_settings()
    producer = create_producer(kafka_settings, client_name="fetcher-scheduler")
    kafka_publisher = KafkaPublisher(producer)
    
    minio_settings = get_minio_settings()
    minio_client = get_minio_client(minio_settings)
    
    print("Starting dynamic fetcher scheduler. Scanning every 300 seconds (5 minutes)...")

    while True:
        try:
            async with AsyncSessionFactory() as session:
                repo = ConnectorRepository(session)
                active_connectors = await repo.get_active()
                
                for connector_model in active_connectors:
                    print(f"Syncing connector: {connector_model.name} ({connector_model.connector_type})")
                    if connector_model.connector_type == ConnectorType.GITHUB:
                        connector = GitHubConnector(
                            connector=connector_model,
                            session=session,
                            minio_client=minio_client,
                            minio_bucket=minio_settings.minio_raw_bucket,
                            kafka_publisher=kafka_publisher,
                            kafka_settings=kafka_settings,
                        )
                        await connector.run()
                
                await session.commit()
                print("All syncs complete.")
        except Exception as e:
            print(f"Error during fetcher sync: {e}")
            
        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(main())
