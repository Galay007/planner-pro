from sqlalchemy import (
    BigInteger, TIMESTAMP, text, DateTime, Column, ForeignKey,String, Integer
)
from ..configs.Database import Base
from sqlalchemy.orm import Mapped, relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .TaskModel import Task
    from .TaskFileModel import TaskFile
    from .ConnectionModel import Connection

class TaskProperty(Base):
    __tablename__ = 'task_properties'

    task_id = Column(BigInteger, ForeignKey('tasks.task_id', ondelete="CASCADE"), nullable=False, primary_key=True, autoincrement=False, info={'passive_deletes': True})
    from_dt = Column(DateTime(timezone=False), nullable=True)
    until_dt = Column(DateTime(timezone=False),nullable=True)
    connection_id = Column(Integer, ForeignKey('connections.id', ondelete='SET NULL'), nullable=True)
    cron_expression = Column(String, nullable=True)
    task_type = Column(String, nullable=False)
    original_path = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    email = Column(String, nullable=True)
    tg_chat_id = Column(String, nullable=True)
    change_dt = Column(DateTime(timezone=False), nullable=False)

    files: Mapped[list["TaskFile"]] = relationship(back_populates="task_props", cascade="all, delete-orphan", lazy="select")
    conn: Mapped["Connection"] = relationship(foreign_keys=[connection_id], lazy="select")
    task: Mapped["Task"] = relationship(back_populates="task_props", lazy="select")


