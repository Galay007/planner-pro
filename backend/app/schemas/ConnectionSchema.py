from typing import Optional
from pydantic import BaseModel, Field


class ConnectionCreate(BaseModel):
    name: str
    conn_type: str
    host:  Optional[str] = None
    port: Optional[int] = None
    db_name: Optional[str] = None
    login: Optional[str] = None
    pass_str: Optional[str] = None
    db_path: Optional[str] = None
   


class ConnectionOut(BaseModel):
    name: str
    conn_type: str
    host: Optional[str] = None
    port: Optional[int]
    db_name: Optional[str]
    login: Optional[str]
    pass_str: Optional[str]
    db_path: Optional[str]


