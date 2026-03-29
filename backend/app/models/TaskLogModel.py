from sqlalchemy import (
    BigInteger, TIMESTAMP, text, DateTime, Column, ForeignKey, String, Integer
)
from sqlalchemy.orm import declarative_base, Mapped, relationship
from ..configs.Database import Base


class TaskLog(Base):
    __tablename__ = 'task_logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_uid = Column(BigInteger, unique=True, nullable=False)
    task_id = Column(BigInteger, nullable=False)
    file_name = Column(String, nullable=True)
    log_text = Column(String, nullable=False)
    worker_id = Column(Integer, nullable=True)
    created_dt = Column(DateTime(timezone=False), nullable=False)
