from fastapi import Depends
from ..repositories.TaskRepository import TaskRepository
from ..models.TaskModel import Task
from datetime import datetime
from typing import List
from .TaskHistService import TaskHistService


class TaskService:
    taskRepository: TaskRepository

    def __init__(
        self, taskRepository: TaskRepository = Depends()
    ) -> None:
        self.taskRepository = taskRepository

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
        new_task.task_deps_uid = self.generate_id(task_id)
        new_task.created_dt = datetime.now()
        new_task.last_change_dt = datetime.now()

        TaskHistService.create_task(task_id,new_task.task_deps_uid)

        return self.taskRepository.create(new_task)


    def get_task_by_id(self,task_id: int) -> Task | None:
        return self.taskRepository.get(task_id)
    
    def generate_id(task_id):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return timestamp*1000+task_id
    
    def get_tasks(self) -> List[Task]:
        return self.taskRepository.get_tasks()


    def update(self, task: Task) -> Task:
        task.last_change_dt = datetime.now()
        return self.taskRepository.update(task)

    def delete(self,id: int) -> None:
        return self.taskRepository.delete(Task(task_id=id))



