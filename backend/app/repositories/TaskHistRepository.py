from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from fastapi import Depends
from sqlalchemy.orm import Session, lazyload

from ..configs.Database import get_orm_connection
from ..models.TaskHistModel import TaskHist

class TaskHistRepository:
    db: Session

    def __init__(
        self, db: Session = Depends(get_orm_connection)
    ) -> None:
        self.db = db

    def get(self, task_uid: int) -> TaskHist:      
        return self.db.query(TaskHist).get(task_uid)

    def get_task_hist(self) -> List[TaskHist]:
        return self.db.query(TaskHist)
    
    def create(self, taskHist: TaskHist) -> TaskHist:
        self.db.add(taskHist)
        self.db.commit()
        self.db.refresh(taskHist)
        return taskHist

    def update(self, taskHist: TaskHist) -> TaskHist:
        self.db.merge(taskHist)
        self.db.commit()
        self.db.refresh(taskHist)
        return taskHist