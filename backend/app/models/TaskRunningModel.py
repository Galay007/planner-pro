from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    select, Column, Integer, BigInteger, Boolean, ForeignKey, String, DateTime, Enum as SQLEnum
)
from ..configs.Database import Base
from enum import Enum
from sqlalchemy.orm import  Mapped, relationship
from pydantic import computed_field

class RunningStatusEnum(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"
    PENDING = "pending"

class TriggerModeEnum(str, Enum):
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    DEPENDED = "depended"

if TYPE_CHECKING:
    from .TaskModel import Task


class TaskRunning(Base):
    __tablename__ = 'task_runnings'
    
    id = Column(BigInteger, primary_key=True)
    task_uid = Column(BigInteger, ForeignKey('tasks.task_uid', ondelete="CASCADE"), info={'passive_deletes': True}, nullable=False)
    task_id = Column(BigInteger, nullable=False)
    parent_uid = Column(BigInteger, nullable=True)
    parent_id = Column(BigInteger, nullable=True)
    trigger_mode = Column(SQLEnum(TriggerModeEnum, native_enum=False, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    schedule_dt = Column(DateTime(timezone=False), nullable=False)
    notifications = Column(Boolean, nullable=False)  
    email = Column(String, nullable=True)
    tg_chat_id = Column(String, nullable=True)
    storage_path = Column(String, nullable=False)
    created_dt = Column(DateTime(timezone=False), nullable=False)
    worker_id = Column(Integer, nullable=True)
    started_dt = Column(DateTime(timezone=False), nullable=True)
    finished_dt = Column(DateTime(timezone=False), nullable=True)
    attempt_count = Column(Integer, nullable=True)
    next_retry_at = Column(DateTime(timezone=False), nullable=True)
    status = Column(SQLEnum(RunningStatusEnum, native_enum=False, values_callable=lambda obj: [e.value for e in obj]), 
                    nullable=False, default=RunningStatusEnum.PENDING )
    
    task: Mapped["Task"] = relationship("Task",foreign_keys=[task_uid],lazy="select",passive_deletes=True)

    @computed_field
    @property
    def task_name(self) -> Optional[str]:
        return self.task.task_name if self.task else None
    
    @computed_field
    @property
    def duration(self) -> Optional[str]:
        try:
            if self.started_dt is not None and self.finished_dt is not None:
                delta_time = self.finished_dt - self.started_dt
                return str(delta_time).split('.')[0]
        except Exception:
            pass
            return None
        
    @computed_field
    @property
    def started_str(self) -> Optional[str]:
        return self.started_dt.strftime("%H:%M:%S") if self.started_dt is not None else None
    
    @computed_field
    @property
    def finished_str(self) -> Optional[str]:
        return self.schedule_dt.strftime("%H:%M:%S") if self.finished_dt is not None else None


    

