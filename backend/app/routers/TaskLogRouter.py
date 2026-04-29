from fastapi import HTTPException, APIRouter, Depends, status
from ..services.TaskLogService import TaskLogService
import logging
from sqlalchemy.orm import Session
from ..configs.Database import get_orm_connection
from ..schemas.TaskLogSchema import TaskLogOut
from typing import Optional, List

logger = logging.getLogger(__name__)

TaskLogRouter = APIRouter(
    prefix="/logs"
)

def get_task_hist_service_repo(db: Session = Depends(get_orm_connection)):
    return TaskLogService(db)

@TaskLogRouter.get("/{task_id}", response_model=List[TaskLogOut])
def get_log(task_id: int, taskLogService: TaskLogService = Depends(get_task_hist_service_repo)):
    task_logs = get_object_from_db(taskLogService, task_id)
    check_is_none(task_logs, task_id)

    return task_logs


def get_object_from_db(service, param):
    return service.get_log_by_id(param)

def check_is_none(object, param):
    if object is None:
        logger.warning(f"Task log '{param}' not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Task log '{param}' not found")
