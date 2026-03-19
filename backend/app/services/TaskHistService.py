from fastapi import Depends
from ..repositories.TaskHistRepository import TaskHistRepository
from ..models.TaskHistModel import TaskHist
from datetime import datetime
from typing import List
from datetime import datetime

class TaskHistService:
    taskHistRepository: TaskHistRepository

    def __init__(
        self, taskHistRepository: TaskHistRepository = Depends()
    ) -> None:
        self.taskHistRepository = taskHistRepository

    def create_task(self,
        task_uid: int,
        task_id: int
        ) -> TaskHist:
        
        new_task_hist = TaskHist(
            task_uid=task_uid,
            task_id=task_id
        )

        return self.taskHistRepository.create(new_task_hist)


    def get_task_hist_by_uid(self,task_uid: int) -> TaskHist | None:
            
        return self.taskHistRepository.get(task_uid)
    
    def get_task_by_id(self,id: int) -> TaskHist | None:
        return self.taskHistRepository.get(id)
    
    def get_task_hist(self) -> List[TaskHist]:
        return self.taskHistRepository.get_task_hist()

    def update(self, taskHist: TaskHist) -> TaskHist:

        return self.taskHistRepository.update(taskHist)
    
    def update_deleted_date(self,task_uid: int,delete_dt: datetime) -> None:
        taskHist = self.get_task_hist_by_uid(task_uid)

        if taskHist:
            taskHist.deleted_dt = delete_dt
            self.update(taskHist)





