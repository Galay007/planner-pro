from sqlalchemy import (
    BigInteger, TIMESTAMP, text, DateTime, Column, ForeignKey,String, Integer
)
from ..configs.Database import Base
from sqlalchemy.orm import Mapped, relationship
from typing import TYPE_CHECKING, Optional, List
from pydantic import computed_field
from cron_descriptor import get_description, Options, CasingTypeEnum, DescriptionTypeEnum, ExpressionDescriptor
from datetime import datetime
from croniter import croniter

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

    files: Mapped[List["TaskFile"]] = relationship(back_populates="task_props", cascade="all, delete-orphan", lazy="select")
    conn: Mapped["Connection"] = relationship(foreign_keys=[connection_id], lazy="select")
    task: Mapped["Task"] = relationship(back_populates="task_props", lazy="select")

    @computed_field
    @property
    def conn_name(self) -> Optional[str]:
        return self.conn.name if self.conn else None
    
    @computed_field
    @property
    def file_names(self) -> List[str]:
        return [f.file_name for f in self.files]
    
    @computed_field
    @property
    def cron_desc(self) -> Optional[str]:        
        if self.cron_expression is not None:
            try:
                options = Options()
                options.casing_type = CasingTypeEnum.Sentence
                options.use_24hour_time_format = True
                options.day_of_week_start_index_zero  = True
                options.locale_code="ru_RU"

                descriptor = ExpressionDescriptor(self.cron_expression, options)
                cron_desc = descriptor.get_description(DescriptionTypeEnum.FULL)

                now = datetime.now()
                sim = croniter(self.cron_expression, now, day_or=False)
                next_runs = [sim.get_next(datetime) for _ in range(5)]

                full_desc = f"Описание: {cron_desc}\n След. 5 запусков: {[r.strftime('%Y-%m-%d %H:%M (%a)') for r in next_runs]}"
                return full_desc
            except Exception:
                return 'Cron выражение не распознано'
        else: return None
            
    


