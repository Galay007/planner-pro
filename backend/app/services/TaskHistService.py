from fastapi import Depends
from ..repositories.TaskHistRepository import TaskHistRepository
from ..models.TaskHistModel import TaskHist
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

class TaskHistService:
    taskHistRepository: TaskHistRepository

    def __init__(
        self, db: Session
    ) -> None:
        self.taskHistRepository = TaskHistRepository(db)       

    def create(self,
        task_uid: int,
        task_id: int,
        dt_time: datetime
        ) -> TaskHist:
        
        new_task_hist = TaskHist(
            task_uid=task_uid,
            task_id=task_id,
            created_dt=dt_time,
            change_dt=dt_time
        )

        return self.taskHistRepository.create(new_task_hist)


    def get_by_uid(self,task_uid: int) -> TaskHist | None:           
        return self.taskHistRepository.get_by_uid(task_uid)
    
    def get_by_id(self,id: int) -> TaskHist | None:
        return self.taskHistRepository.get_by_id(id)
    
    def get_all(self) -> List[TaskHist]:
        return self.taskHistRepository.get_all()

    def update(self, taskHist: TaskHist) -> TaskHist:

        return self.taskHistRepository.update(taskHist)
    
    def update_deleted_date(self,task_uid: int, delete_dt: datetime) -> None:
        taskHist = self.get_by_uid(task_uid)
        taskHist.deleted_dt = delete_dt
        taskHist.change_dt = delete_dt
        self.taskHistRepository.update(taskHist)
    
    def update_last_change_date(self,task_uid:int,change_dt: datetime):
        taskHist = self.get_by_uid(task_uid)
        taskHist.change_dt=change_dt
        self.taskHistRepository.update(taskHist)





