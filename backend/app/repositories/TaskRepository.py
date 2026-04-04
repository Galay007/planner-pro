from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, lazyload, selectinload
from ..models.TaskModel import Task
from ..models.TaskFileModel import TaskFile
from ..models.TaskPropertyModel import TaskProperty
from ..models.ConnectionModel import Connection
from datetime import datetime

class TaskRepository:
    db: Session

    def __init__(
        self, db
    ) -> None:
        self.db = db

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