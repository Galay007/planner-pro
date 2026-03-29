from fastapi import Depends
from ..repositories.TaskLogRepository import TaskLogRepository
from ..models.TaskLogModel import TaskLog
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime


class TaskLogService:
    taskLogRepository: TaskLogRepository

    def __init__(
        self, db: Session
    ) -> None:
        self.taskLogRepository = TaskLogRepository(db)     

    def create(self, taskLog: TaskLog
        ) -> TaskLog:      

        return self.taskLogRepository.c(taskLog)