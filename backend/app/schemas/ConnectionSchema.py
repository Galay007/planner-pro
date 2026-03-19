from typing import Optional
from pydantic import BaseModel, Field


class ConnectionCreate(BaseModel):
    name: str = Field(..., max_length=100)
    conn_type: str = Field(..., max_length=50)      
    host: str = Field(..., max_length=255)
    port: Optional[int] = None
    db_name: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None      
    db_path: Optional[str] = None
   


class ConnectionOut(BaseModel):
    id: int
    name: str
    conn_type: str
    host: str
    port: Optional[int]
    db_name: Optional[str]
    login: Optional[str]
    has_password: Optional[str]
    db_path: Optional[str]
    created_at: Optional[str]

