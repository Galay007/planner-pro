from sqlalchemy import (
    BigInteger, TIMESTAMP, text, DateTime, Column, ForeignKey, String
)
from sqlalchemy.orm import declarative_base, Mapped, relationship
from ..configs.Database import Base


class TaskHist(Base):
    __tablename__ = 'task_hist'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_uid = Column(BigInteger, unique=True, nullable=False)
    task_id = Column(BigInteger, nullable=False)
    task_name = Column(String, nullable=False)
    deleted_dt = Column(DateTime(timezone=False), nullable=True)
    created_dt = Column(DateTime(timezone=False),nullable=False)
    change_dt = Column(DateTime(timezone=False), nullable=False)
    last_run = Column(DateTime(timezone=False), nullable=True)
