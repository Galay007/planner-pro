from datetime import datetime
from sqlalchemy import (
    BigInteger, TIMESTAMP, text
)
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from ..configs.Database import Base


class TaskHist(Base):
    __tablename__ = 'tasks_hist'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_uid: Mapped[int] = mapped_column(BigInteger, primary_key=False, autoincrement=False)
    task_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    deleted_dt: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    created_dt: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), 
        server_default=text('CURRENT_TIMESTAMP')
    )
    last_change_dt: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), 
        server_default=text('CURRENT_TIMESTAMP')
    )
