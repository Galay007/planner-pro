from fastapi import Depends
from ..repositories.TaskHistRepository import TaskHistRepository
from ..models.TaskHistModel import TaskHist
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from .TaskRunningService import TaskRunningService
from .SseService import send_to_client_update
import logging

logger = logging.getLogger(__name__)



class TaskHistService:
    taskHistRepository: TaskHistRepository
    taskRunningService: TaskRunningService
    db: Session

    def __init__(
        self, db: Session
    ) -> None:
        self.taskHistRepository = TaskHistRepository(db) 
        self.taskRunningService =  TaskRunningService(db)    
        self.db = db 
    

    def create(self,
        task_uid: int,
        task_id: int,
        task_name: str,
        owner: str,
        dt_time: datetime
        ) -> TaskHist:
        
        new_task_hist = TaskHist(
            task_uid=task_uid,
            task_id=task_id,
            task_name=task_name,
            task_owner=owner,
            created_dt=dt_time,
            change_dt=dt_time
        )

        self.taskHistRepository.create(new_task_hist)
        self.db.commit()

    def get_by_uid(self, task_uid: int) -> Optional[TaskHist]:           
        return self.taskHistRepository.get_by_uid(task_uid)
    
    def get_by_task_id(self, task_id: int) -> Optional[TaskHist]:
        return self.taskHistRepository.get_by_task_id(task_id)
    
    def get_by_id(self, id: int) -> Optional[TaskHist]:
        return self.taskHistRepository.get_by_id(id)
    
    def get_all(self) -> List[TaskHist]:
        return self.taskHistRepository.get_all()

    def update(self, taskHist: TaskHist) -> TaskHist:
        self.taskRunningService.refresh_runnings()       
        task_hist = self.taskHistRepository.update(taskHist)
        self.db.commit()
        send_to_client_update(event_type="task_update")
        return task_hist
    
    def update_deleted_date_from_task_service(self, task_uid: int, delete_dt: datetime) -> None:
        taskHist = self.get_by_uid(task_uid)
        taskHist.deleted_dt = delete_dt
        taskHist.change_dt = delete_dt
        self.update(taskHist)
    
    def update_change_date_from_task_service(self, task_uid: int, task_name: str, owner: str, change_dt: datetime):
        taskHist = self.get_by_uid(task_uid)
        taskHist.change_dt=change_dt
        taskHist.task_name=task_name
        taskHist.task_owner=owner
        self.update(taskHist)

    def update_change_date_from_task_prop_service(self, task_uid: int, change_dt: datetime):
        taskHist = self.get_by_uid(task_uid)
        taskHist.change_dt=change_dt
        self.update(taskHist)






