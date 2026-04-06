from fastapi import Depends
from ..repositories.TaskRepositoryAPI import TaskRepositoryAPI
from ..models.TaskModel import Task
from ..utils.datetime_utils import DateTimeUtils
from typing import List
from .TaskHistService import TaskHistService


class TaskService:
    taskRepository: TaskRepositoryAPI
    taskHistService: TaskHistService

    def __init__(
        self, taskRepository: TaskRepositoryAPI = Depends()
    ) -> None:
        self.taskRepository = taskRepository
        self.taskHistService = TaskHistService(self.taskRepository.get_db())

    def create_task(self,
        task_id: int,
        task_name: str,
        owner: str,
        task_group: str | None,
        task_deps_id: int | None,
        notifications: bool,
        comment: str | None,

        ) -> Task:
        
        new_task = Task(
            task_id=task_id,
            task_name=task_name,
            owner=owner,
            task_group=task_group,
            task_deps_id=task_deps_id,
            notifications=notifications,
            comment=comment
        )
        new_task.task_uid = self.generate_id(task_id)
        
        dt_time = DateTimeUtils.local_wo_microsec()
        new_task.change_dt = dt_time

        self.taskRepository.create(new_task)
        self.taskHistService.create(new_task.task_uid, new_task.task_id, new_task.task_name, dt_time)

        return new_task


    def get_task_by_id(self,task_id: int) -> Task | None:
        return self.taskRepository.get(task_id)
    
    def generate_id(self, task_id: int) -> int:
        timestamp = DateTimeUtils.now_str()
        return int(timestamp)*1000+task_id
    
    def get_all(self) -> List[Task]:
        return self.taskRepository.get_all()
    
    def get_max_task_id(self) -> int:
        return self.taskRepository.get_max_task_id()

    def update(self, task: Task) -> Task:
        task.change_dt = DateTimeUtils.local_wo_microsec()
        self.taskHistService.update_change_date_from_task_service(task.task_uid, task.task_name, task.change_dt)
        return self.taskRepository.update(task)

    def delete(self,task: Task) -> int:
        # To do удалять папку uploads для task_id и task_type, если она не пустая
        self.taskRepository.delete(task)

        dt_delete = DateTimeUtils.local_wo_microsec()
        self.taskHistService.update_deleted_date_from_task_service(task.task_uid, dt_delete)

    def check_control():
        pass
        #ДОБАВИТЬ ПЕРЕКЛЮЧЕНИЕ CONTROL В OFF ПЕРЕД УДАЛЕНИЕМ TASK_ID, У КОГО TASK_DEPS_ID == TASK_ID deleting

        #ДОБАВИТЬ ПЕРЕКЛЮЧЕНИЕ CONTROL В OFF ПЕРЕД УДАЛЕНИЕМ CONNECTION, У КОГО PLAY И CONNECTION.NAME deleting
        