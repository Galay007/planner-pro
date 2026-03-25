from typing import List, Optional
from sqlalchemy import select
from fastapi import Depends
from sqlalchemy.orm import Session, lazyload, selectinload

from ..configs.Database import get_orm_connection
from ..models.TaskPropertiesModel import TaskProperty


class TaskPropertyRepository:
    db: Session

    def __init__(
        self, db: Session = Depends(get_orm_connection)
    ) -> None:
        self.db = db

    def get(self, task_id: int) -> TaskProperty:      
        return self.db.scalar(
            select(TaskProperty)
            .where(TaskProperty.task_id == task_id)
            .options(selectinload(TaskProperty.files))
        )

    def create(self, taskProperty: TaskProperty) -> TaskProperty:
        self.db.add(taskProperty)
        self.db.flush()
        return taskProperty

    def delete(self, taskProperty: TaskProperty) -> None:
        self.db.delete(taskProperty)

    def get_all(self) -> List[TaskProperty]:
        return self.db.scalars(
            select(TaskProperty)
            .options(selectinload(TaskProperty.files))
            ).all()
    
    def update(self, tasProperty: TaskProperty) -> TaskProperty:
        self.db.merge(tasProperty)
        self.db.flush()
        self.db.refresh(tasProperty)
        return tasProperty
    
    def get_db(self) -> Session:
        return self.db
    
    