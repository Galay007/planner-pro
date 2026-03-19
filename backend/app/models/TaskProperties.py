from sqlalchemy import (
    BigInteger, TIMESTAMP, text, DateTime, Column, ForeignKey,String
)
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from ..configs.Database import Base
from ..utils.datetime_utils import DateTimeUtils


class TaskProperties(Base):
    __tablename__ = 'tasks_hist'

    task_id = Column(BigInteger, ForeignKey('tasks.task_id', ondelete="CASCADE"), nullable=True, primary_key=True, autoincrement=False)
    from_dt = Column(DateTime(timezone=False), nullable=False)
    until_dt = Column(DateTime(timezone=False),nullable=False)
    last_change_dt = Column(DateTime(timezone=False), nullable=False)
    connection_name = Column(String, ForeignKey('connections.name', ondelete='SET NULL'), nullable=True)
    cronn_expression = Column(String, nullable=True)
    task_type = Column(String, nullable=False)
    task_file_path = Column(String, nullable=False)
    email = Column(String, nullable=True)
    tg_chat_id = Column(String, nullable=True)
    last_change_dt = Column(DateTime(timezone=False), nullable=False)
