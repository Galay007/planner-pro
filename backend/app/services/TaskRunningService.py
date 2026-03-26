from fastapi import Depends, HTTPException, status
from ..repositories.taskRunningRepository import TaskRunningRepository
from ..models.TaskRunningModel import TaskRunning, RunningStatusEnum
from ..models.TaskModel import Task
from typing import List
from datetime import datetime
from ..utils.datetime_utils import DateTimeUtils
from .TaskService import TaskService
from .TaskHistService import TaskHistService
from datetime import date, time
from cronsim import CronSim
import logging

logger = logging.getLogger(__name__)

class TaskRunningService:
    taskRunningRepository: TaskRunningRepository
    taskFileService: TaskService
    taskHistService: TaskHistService

    def __init__(
        self, taskRunningRepository: TaskRunningRepository = Depends()
    ) -> None:
        self.taskRunningRepository = taskRunningRepository
        self.taskService = TaskService(self.taskRunningRepository.get_db())
        self.taskHistService = TaskHistService(self.taskRunningRepository.get_db())


    def create(self, taskRunning: TaskRunning):
        self.repo.create(taskRunning)


    def refresh_runnings(self):

        tasks = self.taskService.get_all()

        for task in tasks:

            new_run = TaskRunning(
                task_uid=task.task_uid,
                task_id=task.task_id,
                parent_id=task.task_deps_id,
                notifications=task.notifications,
                email=task.task_props.email,
                tg_chat_id=task.task_props.tg_chat_id,
                storage_path=task.task_props.storage_path,
                created_dt=DateTimeUtils.local_wo_micr(),
                status=RunningStatusEnum.PENDING
            )

            cron_expr = task.task_props.cron_expression

            if task.task_deps_id:
                new_run.parent_uid = self.get_uid(task.task_deps_id)

            if cron_expr:
                updating_date = datetime.now().date()

                today_executions = self.get_today_executions(cron_expr, updating_date)
                
                if today_executions is None:
                    logger.warning(f"Not able to parse cron_expression '{cron_expr}' for task {task.task_id}. {task.task_name}")
                    #TO DO VALIDATE CRON EXPS EARLIER AND SEND CHANGE STATUS THROUGH TASK SERVICE IN DB
                    continue

                for row_execute in today_executions:
                    new_run.schedule_dt = row_execute.date()
                    new_run.schedule_time = row_execute.time()

                    self.create(new_run)


    def get_uid(self, task_id: int) -> int:
        return self.taskHistService.get_by_id(task_id).task_uid
    
    def get_today_executions(cron_expr: str, today_dt: date):
        
        cs = CronSim(cron_expr)

        today_executions = [
            dt for dt, matches in cs.simulate(1440)
            if dt.date() == today_dt
        ]
        return today_executions

    


