from fastapi import Depends
from ..repositories.TaskLogRepository import TaskLogRepository
from ..models.TaskLogModel import TaskLog
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from typing import Optional
import os

class TaskLogService:
    taskLogRepository: TaskLogRepository

    def __init__(
        self, db: Session
    ) -> None:
        self.taskLogRepository = TaskLogRepository(db)     

    def create(self, task_id: int, log_text: str, file_name: Optional[str] = None):

        pid = os.getpid()

        taskLog = TaskLog( 
        task_id = task_id,
        file_name = file_name,
        log_text = log_text,
        pid_id = pid,
        created_dt = datetime.now()
        )

        self.taskLogRepository.create(taskLog)

    def get_log_by_id(self, task_id):
        return self.taskLogRepository.get_by_task_id(task_id)

    def commit(self):
        return self.taskLogRepository.commit()