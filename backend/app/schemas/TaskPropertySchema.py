from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import Depends, UploadFile, File
from datetime import datetime


class TaskPropertyCreate(BaseModel):
    task_id: int
    from_dt: Optional[datetime] 
    until_dt: Optional[datetime] 
    connection_id: Optional[int] 
    cron_expression: Optional[str] 
    task_type: str
    email: Optional[str] 
    tg_chat_id: Optional[str] 
    root_folder: str
    files: List[UploadFile] = File(...)


class TaskPropertyOut(BaseModel):
    task_id: int
    from_dt: Optional[datetime] 
    until_dt: Optional[datetime] 
    connection_id: Optional[int] 
    cron_expression: Optional[str] 
    cron_desc: Optional[str]
    task_type: str
    storage_path: str
    file_names: List[str]
    email: Optional[str] 
    tg_chat_id: Optional[str] 
    conn_name: Optional[str] 

class TaskPropertyIn(BaseModel):
    from_dt: Optional[datetime] 
    until_dt: Optional[datetime] 
    connection_id: Optional[int] 
    cron_expression: Optional[str] 
    task_type: str
    email: Optional[str] 
    tg_chat_id: Optional[str] 
    root_folder: Optional[str] 
    is_manual: Optional[bool]  # true - создан скрипт, false - новые файлы и путь, none - файлы и путь не меняются
    manual_script: Optional[str] 
 

