from sqlalchemy import (
    BigInteger, TIMESTAMP, text, DateTime, Column, ForeignKey, String, Integer
)
from sqlalchemy.orm import declarative_base, Mapped, relationship
from ..configs.Database import Base


class TaskLog(Base):
    __tablename__ = 'task_logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, ForeignKey('tasks.task_id', ondelete="CASCADE"), nullable=False)
    file_name = Column(String, nullable=True)
    log_text = Column(String, nullable=False)
    pid_id = Column(Integer, nullable=True)
    created_dt = Column(DateTime(timezone=False), nullable=False)
