from typing import Optional, List
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
    files: List[UploadFile] = File(...)


class TaskPropertyOut(BaseModel):
    task_id: int
    from_dt: Optional[datetime] = None
    until_dt: Optional[datetime] = None
    connection_id: int
    cron_expression: Optional[str] = None
    task_type: str
    storage_path: str
    file_names: List[str]
    email: Optional[str] = None
    tg_chat_id: Optional[str] = None
    conn_name: Optional[str] = None

class TaskPropertyIn(BaseModel):
    from_dt: Optional[datetime] = None
    until_dt: Optional[datetime] = None
    connection_id: Optional[int] = None
    cron_expression: Optional[str] = None
    task_type: str
    email: Optional[str] = None
    tg_chat_id: Optional[str] = None
    root_folder: Optional[str] = None
    is_manual: Optional[bool] = None # true - создан скрипт, false - новые файлы и путь, none - файлы и путь не меняются
    manual_script: Optional[str] = None
 

