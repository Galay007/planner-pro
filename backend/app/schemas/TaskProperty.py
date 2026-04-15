from typing import Optional
from pydantic import BaseModel, Field
from fastapi import Depends, UploadFile, File
from datetime import datetime


class TaskPropertyCreate(BaseModel):
    task_id: int
    from_dt: Optional[datetime] = None
    until_dt: Optional[datetime] = None
    connection_id: int
    cron_expression: Optional[str] = None
    task_type: str
    email: Optional[str] = None
    tg_chat_id: Optional[str] = None
    root_folder: str
    files: list[UploadFile] = File(...)


class TaskPropertyOut(BaseModel):
    task_id: int
    from_dt: Optional[datetime] = None
    until_dt: Optional[datetime] = None
    connection_id: int
    cron_expression: Optional[str] = None
    task_type: str
    storage_path: str
    file_names: list[str]
    email: Optional[str] = None
    tg_chat_id: Optional[str] = None
    conn_name: Optional[str] = None
 

