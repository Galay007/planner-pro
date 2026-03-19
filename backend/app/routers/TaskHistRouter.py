from fastapi import HTTPException, APIRouter, Depends, status
from ..schemas.TaskSchema import TaskCreate, TaskOut
from ..services.TaskHistService import TaskHistService
import logging

logger = logging.getLogger(__name__)

TaskHistRouter = APIRouter(
    prefix="/task-hist"
)

@TaskHistRouter.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(task_id: int, taskHistService: TaskHistService = Depends()):
    task_hist = taskHistService.get_task_by_id(task_id)
    check_is_none(task_hist)
    
    return taskHistService.delete(task_hist)

@TaskHistRouter.get("/{id}")
def get_task_by_id(id: int, taskHistService: TaskHistService = Depends()):
    task_hist = taskHistService.get_task_by_id(id)
    check_is_none(task_hist)
    
    return task_hist

@TaskHistRouter.get("")
def get_all(taskHistService: TaskHistService = Depends()):
    return taskHistService.get_all()

def check_is_none(param):
    if param is None:
        logger.warning(f"TaskHist '{param}' not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"TaskHist '{param}' not found")



