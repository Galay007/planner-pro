from typing import List, Optional
from sqlalchemy import select, delete
from fastapi import Depends
from sqlalchemy.orm import Session, lazyload, selectinload
from ..models.TaskRunningModel import TaskRunning
from datetime import datetime, timedelta

class TaskRunningRepository:
    db: Session

    def __init__(
        self, db
    ) -> None:
        self.db = db

    def get_by_id(self, id: int) -> TaskRunning:      
        return self.db.query(TaskRunning).filter(TaskRunning.id == id).first()

    def create(self, taskRunning: TaskRunning):
        self.db.add(taskRunning)
        # self.db.flush()

    def get_all(self) -> List[TaskRunning]:
        return self.db.scalars(select(TaskRunning)).all()
    
    def get_db(self) -> Session:
        return self.db
    
    def delete_by_task_id(self, task_id: int, current_dt: datetime) -> None:
        query = (
                delete(TaskRunning)
                .where(TaskRunning.task_id == task_id)
                .where(TaskRunning.schedule_dt >= current_dt.date())
                .where(TaskRunning.schedule_dt < (current_dt.date() + timedelta(days=1)))
                .where(TaskRunning.started_dt.is_(None))
            )
        self.db.execute(query)
    
    