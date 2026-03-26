from typing import List, Optional
from sqlalchemy import select
from fastapi import Depends,HTTPException, status
from sqlalchemy.orm import Session, lazyload, selectinload

from ..configs.Database import get_orm_connection
from ..models.TaskModel import Task
from ..models.TaskPropertiesModel import TaskProperty

class TaskRepository:
    db: Session

    def __init__(
        self, db: Session = Depends(get_orm_connection)
    ) -> None:
        self.db = db

    def get(self, task_id: int) -> Task:           
        return self.db.scalar(
            select(Task)
            .where(Task.task_id==task_id)
            .options(
                selectinload(Task.task_props).selectinload(TaskProperty.files)
            )
        )

    def get_all(self) -> List[Task]:
        return self.db.scalars(
            select(Task)
            .options(
                selectinload(Task.task_props).selectinload(TaskProperty.files)
            )
        ).all()
    
    def create(self, task: Task) -> Task:
        self.db.add(task)
        self.db.flush()
        return task

    def delete(self, task: Task) -> None:
        self.db.delete(task)
        self.db.flush()

    def get_files(self, task_id: int) -> Task:  
        files = []    
        num_files = self.db.scalar(
            select(Task)
            .where(Task.task_id==task_id)
            .options(
                selectinload(Task.task_props).selectinload(TaskProperty.files)
            )
        )
        if num_files.task_props and num_files.task_props.files:
            files = num_files.task_props.files
        
        return files

    def update(self, task: Task) -> Task:
        self.db.merge(task)
        self.db.flush()
        return task
    
    def get_db(self) -> Session:
        return self.db