from typing import List, Optional
from sqlalchemy import select
from fastapi import Depends
from sqlalchemy.orm import Session, lazyload, selectinload
from ..models.TaskRunningModel import TaskRunning
from ..models.TaskModel import Task
from ..models.TaskPropertyModel import TaskProperty


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
        self.db.flush()

    def get_all(self) -> List[TaskRunning]:
        return self.db.scalars(select(TaskRunning)).all()
    
    def get_db(self) -> Session:
        return self.db
    
    def get_all_tasks(self) -> List[Task]:
        return self.db.scalars(
            select(Task)
            .options(
                selectinload(Task.task_props).selectinload(TaskProperty.files)
            )
        ).all()
    
    def get_task_by_task_id_short(self, task_id: int) -> Task:           
        return self.db.scalar(
            select(Task)
            .where(Task.task_id==task_id)
        )
    
    def update_task(self, task: Task) -> Task:
        self.db.merge(task)
        self.db.flush()
        return task