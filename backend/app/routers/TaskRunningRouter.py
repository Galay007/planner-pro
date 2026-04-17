from fastapi import HTTPException, APIRouter, Depends, status
from ..services.TaskRunningService import TaskRunningService
import logging
from sqlalchemy.orm import Session
from ..configs.Database import get_orm_connection
from ..schemas.TaskRunningSchema import TaskRunningOut
from typing import Optional,List

logger = logging.getLogger(__name__)

TaskRunningRouter = APIRouter(
    prefix="/task_runnings"
)

def get_task_hist_service_repo(db: Session = Depends(get_orm_connection)):
    return TaskRunningService(db)

@TaskRunningRouter.get("/{id}")
def get_by_id(id: int,  taskRunningService: TaskRunningService = Depends(get_task_hist_service_repo)):
    task_running = taskRunningService.get_by_id(id)
    check_is_none(task_running, id)
    
    return task_running

@TaskRunningRouter.get("", response_model=List[TaskRunningOut])
def get_all(taskRunningService: TaskRunningService = Depends(get_task_hist_service_repo)):
    taskRunningService.refresh_runnings()
    return taskRunningService.get_all()

def check_is_none(object, param):
    if object is None:
        logger.warning(f"TaskRunning '{param}' not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"TaskRunning '{param}' not found")
    




