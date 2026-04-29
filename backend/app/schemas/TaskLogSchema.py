from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from fastapi import Depends, UploadFile, File
from datetime import datetime



class TaskLogOut(BaseModel):
    task_id: int
    file_name: Optional[str] = None
    log_text: Optional[str] = None
    pid_id: Optional[int] = None
    created_dt: Optional[datetime] = None


