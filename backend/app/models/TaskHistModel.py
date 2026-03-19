from sqlalchemy import (
    BigInteger, TIMESTAMP, text, DateTime, Column, func
)
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from ..configs.Database import Base
from ..utils.datetime_utils import DateTimeUtils


class TaskHist(Base):
    __tablename__ = 'tasks_hist'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_uid = Column(BigInteger, unique=True, nullable=False)
    task_id = Column(BigInteger, nullable=False)
    deleted_dt = Column(DateTime(timezone=False), nullable=True)
    created_dt = Column(DateTime(timezone=False),nullable=False)
    last_change_dt = Column(DateTime(timezone=False), nullable=False)
    last_run = Column(DateTime(timezone=False), nullable=True)
