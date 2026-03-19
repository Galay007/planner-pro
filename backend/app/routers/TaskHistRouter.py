from fastapi import HTTPException, APIRouter, Depends, status
from ..schemas.TaskSchema import TaskCreate, TaskOut
from ..services.TaskHistService import TaskHistService


TaskHistRouter = APIRouter(
    prefix="/task-hist"
)

@TaskHistRouter.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(task_id: int, taskHistService: TaskHistService = Depends()
):
    task = taskHistService.get_task_by_id(task_id)

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found")
    
    return taskHistService.delete(task)

@TaskHistRouter.get("/{id}")
def get_task_by_id(id: int, taskHistService: TaskHistService = Depends()
):
    task_hist = taskHistService.get_task_by_id(id)
    if task_hist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{id}' not found")
    
    return task_hist

@TaskHistRouter.get("/")
def get_task_hist(taskHistService: TaskHistService = Depends()
):
    return taskHistService.get_task_hist()

@TaskHistRouter.put("/{task_id}")
def update_task(task_id: int, data: dict, taskHistService: TaskHistService = Depends()
):
    task = get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    for key, value in data.items():
        if hasattr(task, key):
            setattr(task, key, value)
    
    return taskHistService.update(task)

