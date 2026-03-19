from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from fastapi import Depends,HTTPException,status
from sqlalchemy.orm import Session, lazyload

from ..configs.Database import get_orm_connection
from ..models.TaskHistModel import TaskHist

class TaskHistRepository:
    db: Session

    def __init__(
        self, db: Session = Depends(get_orm_connection)
    ) -> None:
        self.db = db

    def get(self, id: int) -> TaskHist:      
        return self.db.query(TaskHist).filter(TaskHist.id == id).first()

    def get_task_hist(self) -> List[TaskHist]:
        return self.db.query(TaskHist).all()
    
    def create(self, taskHist: TaskHist) -> TaskHist:
        self.db.add(taskHist)

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Connection with name '{taskHist.task_uid}' already exists")
    
        self.db.commit()
        self.db.refresh(taskHist)
        return taskHist

    def update(self, taskHist: TaskHist) -> TaskHist:
        self.db.merge(taskHist)
        self.db.commit()
        self.db.refresh(taskHist)
        return taskHist