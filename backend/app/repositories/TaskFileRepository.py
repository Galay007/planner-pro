from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.orm import Session, lazyload,selectinload
from ..configs.Database import get_orm_connection
from ..models.TaskFileModel import TaskFile
from ..models.TaskModel import Task

class TaskFileRepository:
    db: Session

    def __init__(
        self, db
    ) -> None:
        self.db = db

    def get_by_id(self, id: int) -> TaskFile:      
        return self.db.query(TaskFile).filter(TaskFile.id == id).first()
    
    def get_by_uid(self, task_uid: int) -> TaskFile:      
        return self.db.query(TaskFile).filter(TaskFile.task_uid == task_uid).first()

    def get_all(self) -> List[TaskFile]:
        return self.db.scalars(
            select(TaskFile)
            ).all()
    
    def delete_by_id(self, task_id: int):
        self.db.execute(
        delete(TaskFile).where(TaskFile.task_id==task_id)
        )
        self.db.flush()

    
    def create(self, taskFile: TaskFile) -> TaskFile:
        self.db.add(taskFile)   
        self.db.flush()

    def update(self, taskFile: TaskFile) -> TaskFile:
        self.db.merge(taskFile)
        self.db.flush()
        return taskFile