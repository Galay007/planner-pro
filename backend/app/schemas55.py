from typing import Literal

from pydantic import BaseModel


TaskControl = Literal["play", "stop"]
TaskStatus = Literal["idle", "running", "success", "error"]
TaskFileType = Literal["SQL", "PY", "BAT"]
NotificationChannel = str


class TaskPropertiesBase(BaseModel):
    launch_day: str = ""
    launch_time: str = ""
    end_day: str = ""
    end_time: str = ""
    file_type: TaskFileType = "SQL"
    connection: str = ""
    notification_channel: NotificationChannel = ""
    notification_value: str = ""
    cronExpression: str = ""


class TaskPropertiesRecord(TaskPropertiesBase):
    id: int
    task_id: int


class TaskBase(BaseModel):
    name: str = ""
    group: str = ""
    employee: str = ""
    control: TaskControl = "stop"
    dependency: int | None = None
    status: TaskStatus = "idle"
    notifications: bool = False
    logs: str = ""
    comment: str = ""


class TaskCreate(TaskBase):
    id: int


class TaskReplace(TaskBase):
    pass


class Task(TaskBase):
    id: int
