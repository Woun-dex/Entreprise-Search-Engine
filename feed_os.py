import uuid
import datetime
from opensearchpy import OpenSearch, helpers

client = OpenSearch(
    hosts=[{'host': 'localhost', 'port': 9200}],
    http_compress=True,
    use_ssl=False
)

index_name = "enterprise-search-chunks"

if not client.indices.exists(index=index_name):
    client.indices.create(index=index_name)

now = datetime.datetime.utcnow().isoformat()

docs = [
    {
        "chunk_key": str(uuid.uuid4()),
        "canonical_document_id": str(uuid.uuid4()),
        "connector_id": str(uuid.uuid4()),
        "title": "Introduction to Object-Oriented Design",
        "headings": ["Chapter 1", "Overview"],
        "content": "Object-Oriented Design (OOD) is the process of planning a system of interacting objects for the purpose of solving a software problem.",
        "source_url": "https://github.com/mock/mock-repo/chapter1.md",
        "chunk_index": 0,
        "timestamp": now
    },
    {
        "chunk_key": str(uuid.uuid4()),
        "canonical_document_id": str(uuid.uuid4()),
        "connector_id": str(uuid.uuid4()),
        "title": "Design Patterns",
        "headings": ["Chapter 2", "Factory Pattern"],
        "content": "The Factory Method pattern provides an interface for creating objects in a superclass, but allows subclasses to alter the type of objects that will be created.",
        "source_url": "https://github.com/mock/mock-repo/chapter2.md",
        "chunk_index": 1,
        "timestamp": now
    },
    {
        "chunk_key": str(uuid.uuid4()),
        "canonical_document_id": str(uuid.uuid4()),
        "connector_id": str(uuid.uuid4()),
        "title": "FastAPI Deployment",
        "headings": ["Deployment", "Docker"],
        "content": "To deploy a FastAPI application, you can use Docker. Simply create a Dockerfile that copies your code and runs uvicorn.",
        "source_url": "https://github.com/mock/fastapi-app/deploy.md",
        "chunk_index": 0,
        "timestamp": now
    }
]

bulk_actions = []
for doc in docs:
    bulk_actions.append({
        "_op_type": "index",
        "_index": index_name,
        "_id": doc["chunk_key"],
        "_source": doc
    })

helpers.bulk(client, bulk_actions, refresh=True)
print("Successfully inserted 3 mock documents into OpenSearch!")
