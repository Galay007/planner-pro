from fastapi import Depends
from ..repositories.TaskHistRepository import TaskHistRepository
from ..models.TaskHistModel import TaskHist
from datetime import datetime
from typing import List
from datetime import datetime

class TaskHistService:
    taskRepository: TaskHistRepository

    def __init__(
        self, taskHistRepository: TaskHistRepository = Depends()
    ) -> None:
        self.taskHistRepository = taskHistRepository

    def create_task(self,
        task_uid: int,
        task_id: int,
        deleted_dt: datetime | None,
        created_dt: datetime | None,
        last_change_dt: datetime | None

        ) -> TaskHist:
        
        new_task_hist = TaskHist(
            task_uid=task_uid,
            task_id=task_id,
            deleted_dt=deleted_dt,
            created_dt=created_dt,
            last_change_dt=last_change_dt,
        )

        new_task_hist.created_dt = datetime.now()
        new_task_hist.last_change_dt = datetime.now()

        return self.taskHistRepository.create(new_task_hist)


    def get_task_hist_by_uid(self,task_uid: int) -> TaskHist | None:
            
        return self.taskHistRepository.get(task_uid)
    
    
    def get_task_hist(self) -> List[TaskHist]:
        return self.taskHistRepository.get_task_hist()


    def update(self, taskHist: TaskHist) -> TaskHist:

        return self.taskHistRepository.update(taskHist)
    
    def update_deleted_date(self,task_uid: int,delete_dt: datetime) -> None:
        taskHist = self.get_task_hist_by_uid(task_uid)

        if taskHist:
            taskHist.deleted_dt = delete_dt
            taskHist.last_change_dt = datetime.now()
            self.update(taskHist)





