from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from fastapi import Depends, UploadFile, File
from datetime import datetime



class TaskRunningOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_id: int
    task_name: Optional[str] = None
    parent_uid: Optional[int] = None
    parent_id: Optional[int] = None
    trigger_mode: str
    schedule_dt: datetime
    notifications: bool
    email: Optional[str] = None
    tg_chat_id: Optional[str] = None
    storage_path: str
    created_dt: datetime
    worker_id: Optional[int] = None
    started_str: Optional[str] = None
    finished_str: Optional[str] = None
    duration: Optional[str] = None
    attempt_count: Optional[int] = None
    next_retry_at: Optional[datetime] = None
    status: str

