from fastapi import Depends
from ..repositories.TaskRepositoryAPI import TaskRepositoryAPI
from ..models.TaskModel import Task
from ..utils.DatetimeUtils import DateTimeUtils
from typing import List, Optional
from .TaskHistService import TaskHistService
from .TaskLogService import TaskLogService
from .SseService import send_to_client_update
from datetime import datetime, timedelta
import shutil
from pathlib import Path
from ..configs.Config import settings



class TaskService:
    taskRepository: TaskRepositoryAPI
    taskHistService: TaskHistService
    taskLogService: TaskLogService

    def __init__(
        self, taskRepository: TaskRepositoryAPI = Depends()
    ) -> None:
        self.taskRepository = taskRepository
        self.taskHistService = TaskHistService(self.taskRepository.get_db())
        self.taskLogService = TaskLogService(self.taskRepository.get_db())

    def create_task(self,
        task_id: int,
        task_name: str,
        owner: str,
        task_group: Optional[str],
        task_deps_id: Optional[int],
        notifications: bool,
        comment: Optional[str],

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
        self.taskHistService.create(new_task.task_uid, new_task.task_id, new_task.task_name, new_task.owner, dt_time)

        send_to_client_update(event_type="task_update")

        return new_task


    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        return self.taskRepository.get(task_id)
    
    def generate_id(self, task_id: int) -> int:
        timestamp = DateTimeUtils.now_str()
        return int(timestamp)*1000+task_id
    
    def get_all(self) -> List[Task]:
        tasks = self.taskRepository.get_all()
        return tasks
    
    def get_max_task_id(self) -> int:
        return self.taskRepository.get_max_task_id()

    def update_with_informing(self, task: Task) -> Task:
        task.change_dt = DateTimeUtils.local_wo_microsec()
        self.taskHistService.update_change_date_from_task_service(task.task_uid, task.task_name, task.owner, task.change_dt)
        return self.taskRepository.update(task)
    
    def update_without_informing(self, task: Task) -> Task:
        return self.taskRepository.update(task)

    def delete(self, task: Task) -> int:
        self.taskRepository.delete(task)
        self.task_server_folder_delete(task.task_id)
        dt_delete = DateTimeUtils.local_wo_microsec()
        self.taskHistService.update_deleted_date_from_task_service(task.task_uid, dt_delete)

    def check_control():
        pass
        #ДОБАВИТЬ ПЕРЕКЛЮЧЕНИЕ CONTROL В OFF ПЕРЕД УДАЛЕНИЕМ TASK_ID, У КОГО TASK_DEPS_ID == TASK_ID deleting
        #ДОБАВИТЬ ПЕРЕКЛЮЧЕНИЕ CONTROL В OFF ПЕРЕД УДАЛЕНИЕМ CONNECTION, У КОГО PLAY И CONNECTION.NAME deleting

    def one_time_run(self, task: Task) -> None:
        import subprocess
        from pathlib import Path
        import sys

        task.last_run_at = datetime.now()
        task.run_expire_at = datetime.now() + timedelta(seconds=task.TTL_RUN_SECONDS)
        self.update_with_informing(task)
        
        current_dir = Path(__file__).parent   
        app_dir = current_dir.parent  

        if task.task_props.task_type == 'sql':

            subprocess.Popen([
            sys.executable,
            '-m', 'app.workers.one_time_worker',
            str(task.task_id),
            str(task.task_props.task_type),
            str(task.TTL_RUN_SECONDS),
            task.db_url], 
            cwd=app_dir.parent,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW, #subprocess.CREATE_NEW_CONSOLE,  
            close_fds=True # закрывает ВСЕ файловые дескрипторы родителя
            )

    def task_server_folder_delete(self, task_id: int) -> None:
        server_folder = Path(f'{settings.uploads_dir}/{task_id}')

        if server_folder.exists():
            shutil.rmtree(server_folder)

    def send_log(self, task_id, log_text, PID: int = None, file_name: str = None):
        self.taskLogService.create(task_id, log_text, file_name)

        
