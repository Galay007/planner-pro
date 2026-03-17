from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from fastapi import Depends
from sqlalchemy.orm import Session, lazyload

from ..configs.Database import get_orm_connection
from ..models.TaskModel import Task

class TaskRepository:
    db: Session

    def __init__(
        self, db: Session = Depends(get_orm_connection)
    ) -> None:
        self.db = db

    def get(self, task_id: int) -> Task:      
        return self.db.query(Task).get(task_id)

    def get_tasks(self) -> List[Task]:
        return self.db.query(Task)
    
    def create(self, task: Task) -> Task:
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete(self, task: Task) -> None:
        self.db.delete(task)
        self.db.commit()
        self.db.flush()

    def update(self, task: Task) -> Task:
        self.db.merge(task)
        self.db.commit()
        self.db.refresh(task)
        return task