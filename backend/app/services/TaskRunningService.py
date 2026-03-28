from fastapi import Depends, HTTPException, status
from ..repositories.TaskRunningRepository import TaskRunningRepository
from ..models.TaskRunningModel import TaskRunning, RunningStatusEnum
from ..models.TaskModel import Task, InRunningEnum
from typing import List
from datetime import datetime
from ..utils.datetime_utils import DateTimeUtils
from ..repositories.TaskRepository import TaskRepository
from datetime import date, time
from cronsim import CronSim
import logging
from pathlib import Path
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class TaskRunningService:
    taskRunningRepository: TaskRunningRepository

    def __init__(
        self, db: Session
    ) -> None:
        self.taskRunningRepository = TaskRunningRepository(db)

    def create(self, taskRunning: TaskRunning):
        self.taskRunningRepository.create(taskRunning)

    def update_in_runningt_status(self, task: Task, new_status: InRunningEnum):
        task.in_running = new_status.value
        self.taskRunningRepository.update_task(task)

    def validate_tasks(self, current_dt: datetime) -> list[Task]:
        tasks = self.taskRunningRepository.get_all_tasks()
        validated_tasks_list = []

        for task in tasks:
            if task.control == "on":
                valid_dates = True if task.task_props.from_dt <= current_dt and task.task_props.until_dt else False
                valid_cron = self.is_cron_valid(task.task_props.cron_expression, task.task_id)
                valid_for_running = True if task.in_running == InRunningEnum.CLEARED else False
                valid_task_deps = True if task.task_deps_id is None else False
                valid_storage_path = self.is_path_valid(task.task_props.storage_path, task.task_id)

                if not valid_dates or not valid_cron or not valid_for_running \
                    or not valid_task_deps or not valid_storage_path:

                    logger.warning(f'Task id {task.task_id} has been "ON" but not valid for running task')
                    continue
                elif valid_dates and valid_cron and valid_for_running and valid_task_deps and valid_storage_path:
                    validated_tasks_list.append(task)
        
        return validated_tasks_list
            
    def refresh_runnings(self):
        current_dt = datetime.now()

        valid_tasks_list = self.validate_tasks(current_dt)

        if len(valid_tasks_list) == 0:
            logger.info(f'No tasks for running')
            return

        for task in valid_tasks_list:
            isRunningsSaved = False

            base_fields  = dict(
                task_uid=task.task_uid,
                task_id=task.task_id,
                parent_id=task.task_deps_id,
                notifications=task.notifications,
                email=task.task_props.email,
                tg_chat_id=task.task_props.tg_chat_id,
                storage_path=task.task_props.storage_path,
                created_dt=DateTimeUtils.local_wo_micr(),
                status=RunningStatusEnum.PENDING.value
            )

            cron_expr = task.task_props.cron_expression

            today_executions = self.get_today_executions(cron_expr, current_dt)
            
            if len(today_executions) > 0:
                
                for row_execute in today_executions:
                    new_run = TaskRunning(**base_fields)
                    new_run.schedule_dt = row_execute
                    self.create(new_run)
                
                isRunningsSaved = True
            
            if isRunningsSaved:
                self.update_in_runningt_status(task, InRunningEnum.ADDED)
                


    def get_uid(self, task_id: int) -> int:
        return self.taskHistService.get_by_id(task_id).task_uid
    
    def is_cron_valid(self, expr: str, task_id: int) -> bool:
        try:
            CronSim(expr, datetime.now())
            return True
        except Exception as e:
            logger.error(f'Task id {task_id} has invalid cron expression {expr}')
            return False

    
    def is_path_valid(self, path: str, task_id: int) -> bool:     
        try:
            path_folder = Path(path)
            if path_folder.exists():
                return True
            else:
                return False
        except Exception:
            logger.error(f'Task id {task_id} has invalid path storage {path}')
            return False

    def get_today_executions(self, cron_expr: str, today_dt: datetime) -> list[datetime]:
        cs = CronSim(cron_expr, today_dt)

        today_executions = []
        for _ in range(1440):  # 1440 минут — 24 часа
            dt = next(cs)

            if dt.date() == today_dt.date():
                today_executions.append(dt)

        return today_executions

    


