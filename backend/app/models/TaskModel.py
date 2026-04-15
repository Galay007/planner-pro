from typing import TYPE_CHECKING
from sqlalchemy import (
    Column, Integer, BigInteger, Boolean, CheckConstraint, ForeignKey, String, TIMESTAMP, Text, text, DateTime, Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, relationship
from ..configs.Database import Base
from enum import Enum 
from cronsim import CronSim
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from pydantic import computed_field

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .TaskHistModel import TaskHist
    from .TaskPropertyModel import TaskProperty

class InRunningEnum(str, Enum):
    CLEARED = "cleared"
    TO_CLEAN = "to clean"
    ADDED = "added"

class TaskStatusEnum(str, Enum):
    ACTIVE = "active"
    NOT_ACTIVE = "not active"
    RUNNING = "running"

class Task(Base):
    __tablename__ = 'tasks'
  
    task_uid = Column(BigInteger, primary_key=True, autoincrement=False)
    task_id = Column(BigInteger, unique=True, nullable=False)
    task_name = Column(String, nullable=False)
    on_control = Column(String, nullable=False, default='off')
    owner = Column(String, nullable=False)
    task_group = Column(String, nullable=True)
    task_deps_id = Column(BigInteger,ForeignKey('tasks.task_id', ondelete='SET NULL'),nullable=True)
    status = Column(SQLEnum(TaskStatusEnum, native_enum=False, values_callable=lambda obj: [e.value for e in obj]), 
                    nullable=False, default=TaskStatusEnum.NOT_ACTIVE)
    notifications = Column(Boolean, nullable=False, default=False)
    log_text = Column(Text,nullable=True)
    comment = Column(Text,nullable=True) 
    in_running = Column(SQLEnum(InRunningEnum, native_enum=False, values_callable=lambda obj: [e.value for e in obj]), 
                        nullable=False, default=InRunningEnum.CLEARED)
    added_running_dt = Column(DateTime(timezone=False), nullable=True )
    change_dt = Column(DateTime(timezone=False), nullable=False )
    last_run_at = Column(DateTime(timezone=False), nullable=True )
    edit_expire_at = Column(DateTime(timezone=False), nullable=False, default='1900-01-01')
    run_expire_at = Column(DateTime(timezone=False), nullable=False, default='1900-01-01')

    task_props: Mapped["TaskProperty"] = relationship(back_populates="task", cascade="all, delete-orphan", lazy="select", passive_deletes=True )

    TTL_EDIT_SECONDS = 30
    TTL_RUN_SECONDS = 30

    @computed_field
    @property
    def schedule_cron(self) -> Optional[str]:
        if self.task_deps_id is None:
            return self.task_props.cron_expression if self.task_props else None
        else:
            return None
        
    @computed_field
    @property
    def schedule_depend(self) -> Optional[str]:    
        if self.task_deps_id:
            return f"После id {self.task_deps_id}"
        else:
            return None
    
    @computed_field
    @property
    def next_run_at(self) -> Optional[str]:
        try:
            if self.on_control == 'on' and self.task_deps_id is None:
                cs = CronSim(self.task_props.cron_expression, datetime.now())
                dt = next(cs)
                return dt.strftime("%d.%m.%Y %H:%M:%S")
            return None
        except Exception:
            return None
    
    @computed_field
    @property
    def db_url(self) -> Optional[str]:
        return self.task_props.conn.build_sqlalchemy_url() if self.task_props else None
      

    def return_id_uid(self):
            return {
                "task_id": self.task_id.__str__(),
                "task_uid": self.task_uid.__str__()
            }

    def is_cron_valid(self, expr: str, task_id: int) -> bool:
        try:
            CronSim(expr, datetime.now())
            return True
        except Exception as e:
            logger.error(f'Task id {task_id} has invalid cron expression {expr}')
            return False
  
    def is_path_valid(self, path: str, task_id: int) -> bool:     
        try:
            path_folder = Path(path)
            if path_folder.exists():
                return True
            else:
                return False
        except Exception:
            logger.error(f'Task id {task_id} has invalid path storage {path}')
            return False

    def get_today_executions(self, cron_expr: str, today_dt: datetime) -> list[datetime]:
        cs = CronSim(cron_expr, today_dt)

        today_executions = []
        for _ in range(1440):  # 1440 минут — 24 часа
            dt = next(cs)

            if dt.date() == today_dt.date():
                today_executions.append(dt)

        return today_executions
  
    def check_valid_before_on_control(self) -> tuple[Boolean,str]:
        if self.task_deps_id is None:
            if self.is_to_clean() or not all(self.schedule_execute_params.values()):
                
                first_key_false = 'valid_to_clean'
                
                if not all(self.schedule_execute_params.values()):
                    first_key_false = next((key for key, value in self.schedule_execute_params.items() if not value), None)
                
                message = f'Task_id {self.task_id} can not be "ON" due to not {first_key_false}'
                logger.warning(message)
                
                return False, message
        else:
            if not all(self.depended_execute_params.values()):
                first_key_false = next((key for key, value in self.depended_execute_params.items() if not value), None)
                message = f'Depended task_id {self.task_id} can not be "ON" due to not {first_key_false}'
                logger.warning(message)
                
                return False, message
        return True, '' 
    
    def check_valid_for_manual_execute(self) -> tuple[Boolean,str]:
        if not all(self.manual_execute_params.values()):
            first_key_false = next((key for key, value in self.manual_execute_params.items() if not value), None)
            message = f'One-time execute for task_id {self.task_id} can not be run due to not {first_key_false}'
            logger.warning(message)
                
            return False, message
        
        return True, ''

    @property
    def manual_execute_params(self):
        return {
            "valid_storage_path": self.is_storage_path(),
            "valid_connection": self.is_connection()
        }
    
    @property
    def schedule_future_execute_params(self):
        return {
            "valid_cron": self.is_cron(),
            "valid_storage_path": self.is_storage_path(),
            "valid_connection": self.is_connection()
        }

    @property
    def depended_execute_params(self):
        return {
            "valid_cron": not self.is_cron(),
            "valid_storage_path": self.is_storage_path(),
            "valid_connection": self.is_connection()
        }

    @property
    def schedule_execute_params(self):
        return {
            "valid_dates": self.is_dates(),
            "valid_now_dates": self.is_in_now_dates(),
            "valid_no_past": self.is_no_past(),
            "valid_no_depend": self.is_no_depend(),
            "valid_cron": self.is_cron(),
            "valid_storage_path": self.is_storage_path(),
            "valid_connection": self.is_connection()
        }

    def is_dates(self) -> Boolean:
        try:
            return True if self.task_props.until_dt >= self.task_props.from_dt else False
        except Exception:
            return False
    
    def is_no_past(self) -> Boolean:
        try:
            return True if self.task_props.from_dt >= self.task_props.from_dt else False
        except Exception:
            return False
        
    def is_in_now_dates(self) -> Boolean:
        try:
            current_dt = datetime.now()
            return True if self.task_props.from_dt <= current_dt and self.task_props.until_dt >= current_dt else False
        except Exception:
            return False
    
    def is_in_future(self) -> Boolean:
        try:
            current_dt = datetime.now()
            return True if self.task_props.until_dt > current_dt and self.task_props.from_dt > current_dt else False
        except Exception:
            return False  
        
    def is_no_depend(self) -> Boolean:
        try:
            return True if self.task_deps_id is None else False
        except Exception:
            return False
            
    def is_depend(self) -> Boolean:
        try:
            return True if self.task_deps_id is not None else False
        except Exception:
            return False
    
    def is_added(self) -> Boolean:
        try:
            return True if self.in_running == InRunningEnum.ADDED  else False
        except Exception:
            return False 
    
    def is_cleared(self) -> Boolean:
        try:
            return True if self.in_running == InRunningEnum.CLEARED  else False
        except Exception:
            return False
        
    def is_to_clean(self) -> Boolean:
        try:
            return True if self.in_running == InRunningEnum.TO_CLEAN  else False
        except Exception:
            return False
    
    def is_cron(self) -> Boolean:
        try:
            return self.is_cron_valid(self.task_props.cron_expression, self.task_id)
        except Exception:
            return False   
        
    def is_storage_path(self) -> Boolean:
        try:
            return self.is_path_valid(self.task_props.storage_path, self.task_id)
        except Exception:
            return False
        
    def is_connection(self) -> Boolean:
        try:
            return True if self.task_props.connection_id is not None else False
        except Exception:
            return False
    
    def is_running(self) -> Boolean:
        return True if self.in_running == TaskStatusEnum.RUNNING  else False

