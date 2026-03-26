from fastapi import Depends
from ..repositories.TaskRepository import TaskRepository
from ..models.TaskModel import Task
from ..utils.datetime_utils import DateTimeUtils
from typing import List
from .TaskHistService import TaskHistService


class TaskService:
    taskRepository: TaskRepository
    taskHistService: TaskHistService

    def __init__(
        self, taskRepository: TaskRepository = Depends()
    ) -> None:
        self.taskRepository = taskRepository
        self.taskHistService = TaskHistService(self.taskRepository.get_db())

    def create_task(self,
        task_id: int,
        task_name: str,
        task_control: str,
        owner: str,
        task_group: str | None,
        task_deps_id: int | None,
        notifications: bool,
        comment: str | None,

        ) -> Task:
        
        new_task = Task(
            task_id=task_id,
            task_name=task_name,
            task_control=task_control,
            owner=owner,
            task_group=task_group,
            task_deps_id=task_deps_id,
            notifications=notifications,
            comment=comment
        )
        new_task.task_uid = self.generate_id(task_id)
        
        dt_time = DateTimeUtils.local_wo_micr()
        new_task.change_dt = dt_time

        self.taskRepository.create(new_task)
        self.taskHistService.create(new_task.task_uid, new_task.task_id, dt_time)

        return new_task


    def get_task_by_id(self,task_id: int) -> Task | None:
        return self.taskRepository.get(task_id)
    
    def generate_id(self, task_id: int) -> int:
        timestamp = DateTimeUtils.now_str()
        return int(timestamp)*1000+task_id
    
    def get_all(self) -> List[Task]:
        return self.taskRepository.get_all()


    def update(self, task: Task) -> Task:
        task.change_dt = DateTimeUtils.local_wo_micr()
        self.taskHistService.update_last_change_date(task.task_uid, task.change_dt)
        return self.taskRepository.update(task)

    def delete(self,task: Task) -> int:
        # To do удалять папку uploads для task_id и task_type, если она не пустая
        self.taskRepository.delete(task)

        
        task_temp = self.get_task_by_id(task.task_id)
        if task_temp:
            print (task_temp.task_id)

        dt_delete = DateTimeUtils.local_wo_micr()
        self.taskHistService.update_deleted_date(task.task_uid, dt_delete)

    def check_control():
        pass
        #ДОБАВИТЬ ПЕРЕКЛЮЧЕНИЕ CONTROL В OFF ПЕРЕД УДАЛЕНИЕМ TASK_ID, У КОГО TASK_DEPS_ID == TASK_ID deleting

        #ДОБАВИТЬ ПЕРЕКЛЮЧЕНИЕ CONTROL В OFF ПЕРЕД УДАЛЕНИЕМ CONNECTION, У КОГО PLAY И CONNECTION.NAME deleting
        