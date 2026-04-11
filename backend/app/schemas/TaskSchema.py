from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, computed_field
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
    task_deps_id: Optional[int] = None
    status: str
    notifications: bool
    comment: Optional[str] = None
 
class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_id: int
    task_name: str
    on_control: str
    owner: str
    schedule: Optional[str] = None
    next_run: Optional[str] = None
    task_group: Optional[str] = None
    task_deps_id: Optional[int] = None
    status: str
    notifications: bool
    comment: Optional[str] = None




    