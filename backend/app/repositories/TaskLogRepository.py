from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, lazyload, selectinload
from ..models.TaskLogModel import TaskLog

class TaskLogRepository:
    db: Session

    def __init__(
        self, db
    ) -> None:
        self.db = db

    def create(self, taskLog: TaskLog) -> TaskLog:
        self.db.add(taskLog)   
        self.db.flush()
        return taskLog

    def get_all_logs(self) -> List[TaskLog]:
            return self.db.scalars(select(TaskLog)).all()
        
    def get_log_by_task_id(self, task_id: int) -> TaskLog:           
        return self.db.scalar(
            select(TaskLog)
            .where(TaskLog.task_id==task_id)
        )
    
    def update_log(self, taskLog: TaskLog) -> TaskLog:
        self.db.merge(taskLog)
        self.db.flush()
        return taskLog
    
    def get_by_task_id(self, task_id: int) -> List[TaskLog]:      
        return self.db.scalars(
            select(TaskLog)
            .where(TaskLog.task_id == task_id)
            .order_by(TaskLog.created_dt.desc())
        ).all()
    
    def commit(self):
         self.db.commit()