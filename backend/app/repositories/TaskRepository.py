from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from fastapi import Depends,HTTPException, status
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
         # self.db.query(Task).get(task_id)  если поле PK
        return self.db.query(Task).filter(Task.task_id == task_id).first()

    def get_all(self) -> List[Task]:
      
        return self.db.query(Task).all()
    
    def create(self, task: Task) -> Task:
        self.db.add(task)
        self.db.flush()
        return task

    def delete(self, task: Task) -> None:
        self.db.delete(task)
        self.db.flush()
        # task = self.db.get(Task, task.task_uid)
        # if task:
        #     self.db.delete(task)
        #     self.db.commit()


    def update(self, task: Task) -> Task:
        self.db.merge(task)
        self.db.flush()
        return task