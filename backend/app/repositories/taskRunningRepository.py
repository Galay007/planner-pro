from typing import List, Optional
from sqlalchemy import select
from fastapi import Depends
from sqlalchemy.orm import Session, lazyload

from ..configs.Database import get_orm_connection
from ..models.TaskRunningModel import TaskRunning


class TaskRunningRepository:
    db: Session

    def __init__(
        self, db
    ) -> None:
        self.db = db

    def get_by_id(self, id: int) -> TaskRunning:      
        return self.db.query(TaskRunning).filter(TaskRunning.id == id).first()

    def create(self, taskRunning: TaskRunning) -> TaskRunning:
        self.db.add(taskRunning)
        self.db.flush()
        self.db.refresh()
        return taskRunning

    def get_all(self) -> List[TaskRunning]:
        return self.db.scalars(select(TaskRunning)).all()