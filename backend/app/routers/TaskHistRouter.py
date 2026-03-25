from fastapi import HTTPException, APIRouter, Depends, status
from ..schemas.TaskSchema import TaskCreate, TaskOut
from ..services.TaskHistService import TaskHistService
import logging
from sqlalchemy.orm import Session, lazyload
from ..configs.Database import get_orm_connection

logger = logging.getLogger(__name__)

TaskHistRouter = APIRouter(
    prefix="/task_hist"
)

def get_task_hist_service_repo(db: Session = Depends(get_orm_connection)):
    return TaskHistService(db)

@TaskHistRouter.get("/{id}")
def get_by_id(id: int,  taskHistService: TaskHistService = Depends(get_task_hist_service_repo)):
    task_hist = taskHistService.get_by_id(id)
    check_is_none(task_hist, id)
    
    return task_hist

@TaskHistRouter.get("")
def get_all(taskHistService: TaskHistService = Depends(get_task_hist_service_repo)):
    return taskHistService.get_all()

def check_is_none(object, param):
    if object is None:
        logger.warning(f"TaskHist '{param}' not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"TaskHist '{param}' not found")
    




