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

    def get_by_id(self, id: int) -> TaskHist:      
        return self.db.query(TaskHist).filter(TaskHist.id == id).first()
    
    def get_by_uid(self, task_uid: int) -> TaskHist:      
        return self.db.query(TaskHist).filter(TaskHist.task_uid == task_uid).first()

    def get_all(self) -> List[TaskHist]:
        return self.db.query(TaskHist).all()
    
    def create(self, taskHist: TaskHist) -> TaskHist:
        self.db.add(taskHist)   
        self.db.flush()
        return taskHist

    def update(self, taskHist: TaskHist) -> TaskHist:
        self.db.merge(taskHist)
        self.db.flush()
        return taskHist