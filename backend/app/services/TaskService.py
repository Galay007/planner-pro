from fastapi import Depends
from ..repositories.TaskRepository import TaskRepository
from ..models.TaskModel import Task
from datetime import datetime
from typing import List
from .TaskHistService import TaskHistService


class TaskService:
    taskRepository: TaskRepository
    taskHistRepository: TaskHistService

    def __init__(
        self, taskRepository: TaskRepository = Depends(),
        taskHistRepository: TaskHistService = Depends()
    ) -> None:
        self.taskRepository = taskRepository
        self.taskHistRepository = taskHistRepository

    def create_task(self,
        task_id: int,
        control: str,
        owner: str,
        task_group: str | None,
        task_deps_id: int | None,
        task_deps_uid: int | None,
        status: str,
        notifications: bool,
        comment: str | None,

        ) -> Task:
        
        new_task = Task(
            task_id=task_id,
            control=control,
            owner=owner,
            task_group=task_group,
            task_deps_id=task_deps_id,
            task_deps_uid=task_deps_uid,
            status=status,
            notifications=notifications,
            comment=comment
        )
        new_task.task_uid = self.generate_id(task_id)
        
        self.taskRepository.create(new_task)
        self.taskHistRepository.create_task(new_task.task_uid,new_task.task_id)

        return new_task


    def get_task_by_id(self,task_id: int) -> Task | None:
        return self.taskRepository.get(task_id)
    
    def generate_id(self, task_id: int) -> int:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return int(timestamp)*1000+task_id
    
    def get_tasks(self) -> List[Task]:
        return self.taskRepository.get_tasks()


    def update(self, task: Task) -> Task:
        return self.taskRepository.update(task)

    def delete(self,task: Task) -> None:
        return self.taskRepository.delete(task)



