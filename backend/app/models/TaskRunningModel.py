from typing import TYPE_CHECKING
from sqlalchemy import (
    Column, Integer, BigInteger, Boolean, CheckConstraint, ForeignKey, String, TIMESTAMP, Text, text, DateTime, Date, Time, Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, relationship
from ..configs.Database import Base
from enum import Enum

class RunningStatusEnum(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"


class TaskRunning(Base):
    __tablename__ = 'task_runnings'
    
    id = Column(BigInteger, primary_key=True)
    task_uid = Column(BigInteger, nullable=False)
    task_id = Column(BigInteger, nullable=False)
    parent_uid = Column(BigInteger, nullable=True)
    parent_id = Column(BigInteger, nullable=True)
    schedule_dt = Column(DateTime(timezone=False), nullable=False)
    notifications = Column(Boolean, nullable=False)  
    email = Column(String, nullable=True)
    tg_chat_id = Column(String, nullable=True)
    storage_path = Column(String, nullable=False)
    created_dt = Column(DateTime(timezone=False), nullable=False)
    started_dt = Column(DateTime(timezone=False), nullable=True)
    finished_dt = Column(DateTime(timezone=False), nullable=True)
    status = Column(SQLEnum(RunningStatusEnum, native_enum=False, values_callable=lambda obj: [e.value for e in obj]), 
                    nullable=False, default=RunningStatusEnum.PENDING )

    

