from sqlalchemy import (
    Column, Integer, BigInteger, Boolean, CheckConstraint, ForeignKey, String, TIMESTAMP, Text, text, DateTime, func
)
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from ..configs.Database import Base


class Task(Base):
    __tablename__ = 'tasks'
  
    task_uid = Column(BigInteger, primary_key=True, autoincrement=False)
    task_id = Column(BigInteger, unique=True, nullable=False)
    control = Column(String, nullable=False, default='stop')
    owner = Column(String, nullable=False)
    task_group = Column(String, nullable=True)
    last_run = Column(TIMESTAMP(timezone=False))
    schedule = Column(String, nullable=True)
    cron_expression = Column(String, nullable=True)
    task_deps_id = Column(BigInteger,ForeignKey('tasks.task_id', ondelete='SET NULL'),nullable=True)
    task_deps_uid = Column(BigInteger,nullable=True)
    status = Column(String, nullable=False, default='not active')
    notifications = Column(Boolean, nullable=False, default=False)
    logs_text = Column(Text,nullable=True)
    comment = Column(Text,nullable=True)
    created_dt = Column(DateTime(timezone=False),server_default=func.now()) 
    last_change_dt = Column(DateTime(timezone=False), server_default=func.now(),onupdate=func.now() )

    __table_args__ = (
        CheckConstraint("control IN ('play', 'stop')", name='check_control'),
        CheckConstraint("status IN ('not active', 'running', 'success', 'error')", name='check_status'),
    )
