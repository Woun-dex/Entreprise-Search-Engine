from typing import List
from uuid import UUID

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from ConnectorsService.db.session import AsyncSessionFactory, AsyncSession
from ConnectorsService.models.connector import ConnectorModel
from ConnectorsService.models.enums import ConnectorType, ConnectorStatus
from ConnectorsService.repositories.connector_repository import ConnectorRepository
from ConnectorsService.schema.connector import Connector


async def get_db():
    async with AsyncSessionFactory() as session:
        yield session

app = FastAPI(title="Connectors API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/connectors", response_model=List[Connector])
async def list_connectors(session: AsyncSession = Depends(get_db)):
    repo = ConnectorRepository(session)
    connectors = await repo.get_all()
    return connectors

@app.post("/connectors/github", response_model=Connector)
async def create_github_connector(url: str, session: AsyncSession = Depends(get_db)):
    repo = ConnectorRepository(session)
    
    # Simple validation
    if not url.startswith("https://github.com/"):
        raise HTTPException(status_code=400, detail="Must be a valid GitHub URL")
        
    parts = url.rstrip("/").split("/")
    if len(parts) < 5:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL format")
        
    owner = parts[3]
    repo_name = parts[4]
    name = f"{owner}/{repo_name}"
    
    connector = ConnectorModel(
        connector_type=ConnectorType.GITHUB,
        name=name,
        source_url=url,
        branch_name="main",
        status=ConnectorStatus.ACTIVE
    )
    
    await repo.add(connector)
    await session.commit()
    await session.refresh(connector)
    
    return connector

@app.delete("/connectors/{connector_id}")
async def delete_connector(connector_id: UUID, session: AsyncSession = Depends(get_db)):
    repo = ConnectorRepository(session)
    deleted = await repo.delete(connector_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Connector not found")
    await session.commit()
    return {"message": "Connector deleted successfully"}
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
