from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class TaskCreate(BaseModel):
    task_id: int
    task_name: str
    owner: str
    task_group: Optional[str] = None
    task_deps_id: Optional[int] = None
    notifications: Optional[bool] = None
    comment: Optional[str] = None


class Task(BaseModel):
    task_uid: int
    task_id: int
    task_name: str
    on_control: str
    owner: str
    task_group: Optional[str] = None
    schedule: Optional[str] = None
    task_deps_id: Optional[int] = None
    status: str
    notifications: bool
    log_text: Optional[str] = None
    comment: Optional[str] = None
    in_running: Optional[str]
    added_running_dt: Optional[str] = None
    change_dt: Optional[datetime] = None

class TaskOut(Task):
    task_id: int
    task_name: str
    on_control: str
    owner: str
    task_group: Optional[str] = None
    schedule: Optional[str] = None
    task_deps_id: Optional[int] = None
    status: str
    notifications: bool
    comment: Optional[str] = None
 



    