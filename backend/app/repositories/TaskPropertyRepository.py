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

    def get(self, name: str) -> TaskProperty:      
        return self.db.query(TaskProperty).filter(TaskProperty.name == name).first()

    def create(self, taskProperty: TaskProperty) -> TaskProperty:
        self.db.add(taskProperty)
        self.db.flush()
        return taskProperty

    def delete(self, taskProperty: TaskProperty) -> None:
        self.db.delete(taskProperty)

    def get_all(self) -> List[TaskProperty]:
        return self.db.scalars(select(TaskProperty).options(selectinload(TaskProperty.files))).all()
    
    def get_db(self) -> Session:
        return self.db