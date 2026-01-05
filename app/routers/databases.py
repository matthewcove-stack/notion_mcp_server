"""
Database management endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/databases", tags=["databases"])


class DatabaseInfo(BaseModel):
    id: str
    title: str
    url: Optional[str] = None


class DatabaseSchema(BaseModel):
    id: str
    title: str
    properties: dict
    url: Optional[str] = None


class DiscoverRequest(BaseModel):
    name: str


class UpdateSchemaRequest(BaseModel):
    properties: dict


@router.get("", response_model=List[DatabaseInfo])
async def list_databases():
    """
    List configured databases
    """
    # TODO: Implement actual Notion API call to list databases
    return []


@router.post("/discover", response_model=List[DatabaseInfo])
async def discover_databases(request: DiscoverRequest):
    """
    Find databases by name
    """
    # TODO: Implement actual Notion API search for databases
    return []


@router.get("/{db_id}", response_model=DatabaseSchema)
async def get_database(db_id: str):
    """
    Get database schema
    """
    # TODO: Implement actual Notion API call to get database
    raise HTTPException(status_code=404, detail=f"Database {db_id} not found")


@router.patch("/{db_id}", response_model=DatabaseSchema)
async def update_database(db_id: str, request: UpdateSchemaRequest):
    """
    Update database schema
    """
    # TODO: Implement actual Notion API call to update database
    raise HTTPException(status_code=404, detail=f"Database {db_id} not found")

