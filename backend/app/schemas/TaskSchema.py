from typing import Optional
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    task_id: int
    control: str
    owner: str
    task_group: Optional[str] = None
    task_deps_id: Optional[int] = None
    task_deps_uid: Optional[int] = None
    status: str
    notifications: bool
    comment: Optional[str] = None


class TaskOut(BaseModel):
    task_id: int
    task_uid: int
    control: str
    owner: str
    task_group: Optional[str] = None
    task_deps_id: Optional[int] = None
    task_deps_uid: Optional[int] = None
    status: str
    notifications: bool
    comment: Optional[str] = None