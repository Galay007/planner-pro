from typing import Optional
from pydantic import BaseModel, Field


class ConnectionSchem(BaseModel):
    name: str
    conn_type: str
    host:  Optional[str] = None
    port: Optional[int] = None
    db_name: Optional[str] = None
    login: Optional[str] = None
    pass_str: Optional[str] = None
    db_path: Optional[str] = None
   


