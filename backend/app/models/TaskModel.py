from typing import TYPE_CHECKING
from sqlalchemy import (
    Column, Integer, BigInteger, Boolean, CheckConstraint, ForeignKey, String, TIMESTAMP, Text, text, DateTime, func
)
from sqlalchemy.orm import Mapped, relationship
from ..configs.Database import Base

if TYPE_CHECKING:
    from .TaskHistModel import TaskHist
    from .TaskPropertiesModel import TaskProperty

class Task(Base):
    __tablename__ = 'tasks'
  
    task_uid = Column(BigInteger, primary_key=True, autoincrement=False)
    task_id = Column(BigInteger, unique=True, nullable=False)
    control = Column(String, nullable=False, default='stop')
    owner = Column(String, nullable=False)
    task_group = Column(String, nullable=True)
    schedule = Column(String, nullable=True)
    task_deps_id = Column(BigInteger,ForeignKey('tasks.task_id', ondelete='SET NULL'),nullable=True)
    status = Column(String, nullable=False, default='not active')
    notifications = Column(Boolean, nullable=False, default=False)
    log_text = Column(Text,nullable=True)
    comment = Column(Text,nullable=True) 
    change_dt = Column(DateTime(timezone=False), nullable=False )

    __table_args__ = (
        CheckConstraint("control IN ('play', 'stop')", name='check_control'),
        CheckConstraint("status IN ('not active', 'running', 'success', 'error')", name='check_status'),
    )

    task_props: Mapped["TaskProperty"] = relationship(back_populates="task", lazy="select", passive_deletes=True )

    def return_id_uid(self):
            return {
                "task_id": self.task_id.__str__(),
                "task_uid": self.task_uid.__str__()
            }