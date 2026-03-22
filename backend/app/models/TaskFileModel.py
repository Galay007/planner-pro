from sqlalchemy import (
    BigInteger, TIMESTAMP, text, DateTime, Column, ForeignKey, String, Integer
)
from ..configs.Database import Base
from sqlalchemy.orm import declarative_base, Mapped, relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .TaskPropertiesModel import TaskProperty

class TaskFile(Base):
    __tablename__ = "task_files"

    id = Column(Integer, primary_key=True)
    task_id = Column(BigInteger, ForeignKey("task_properties.task_id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String, nullable=False)
    file_path  = Column(String, nullable=False)
    change_dt = Column(DateTime(timezone=False), nullable=False)

    task_props: Mapped["TaskProperty"] = relationship(back_populates="files", lazy="select")