from typing import TYPE_CHECKING
from sqlalchemy import (
    Column, Integer, BigInteger, Boolean, CheckConstraint, ForeignKey, String, TIMESTAMP, Text, text, DateTime, Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, relationship
from ..configs.Database import Base
from enum import Enum 

if TYPE_CHECKING:
    from .TaskHistModel import TaskHist
    from .TaskPropertyModel import TaskProperty

class InRunningEnum(str, Enum):
    CLEARED = "cleared"
    TO_CLEAN = "to clean"
    ADDED = "added"

class TaskStatusEnum(str, Enum):
    ACTIVE = "active"
    NOT_ACTIVE = "not active"
    RUNNING = "running"

class Task(Base):
    __tablename__ = 'tasks'
  
    task_uid = Column(BigInteger, primary_key=True, autoincrement=False)
    task_id = Column(BigInteger, unique=True, nullable=False)
    task_name = Column(String, nullable=False)
    control = Column(String, nullable=False, default='off')
    owner = Column(String, nullable=False)
    task_group = Column(String, nullable=True)
    schedule = Column(String, nullable=True)
    task_deps_id = Column(BigInteger,ForeignKey('tasks.task_id', ondelete='SET NULL'),nullable=True)
    status = Column(SQLEnum(TaskStatusEnum, native_enum=False, values_callable=lambda obj: [e.value for e in obj]), 
                    nullable=False, default=TaskStatusEnum.NOT_ACTIVE)
    notifications = Column(Boolean, nullable=False, default=False)
    log_text = Column(Text,nullable=True)
    comment = Column(Text,nullable=True) 
    in_running = Column(SQLEnum(InRunningEnum, native_enum=False, values_callable=lambda obj: [e.value for e in obj]), 
                        nullable=False, default=InRunningEnum.CLEARED)
    added_running_dt = Column(DateTime(timezone=False), nullable=True )
    change_dt = Column(DateTime(timezone=False), nullable=False )

    

    task_props: Mapped["TaskProperty"] = relationship(back_populates="task", cascade="all, delete-orphan", lazy="select", passive_deletes=True )

    def return_id_uid(self):
            return {
                "task_id": self.task_id.__str__(),
                "task_uid": self.task_uid.__str__()
            }