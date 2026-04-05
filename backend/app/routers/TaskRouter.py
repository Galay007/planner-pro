from fastapi import HTTPException, APIRouter, Depends, status
from ..models.TaskModel import TaskStatusEnum, InRunningEnum
from ..schemas.TaskSchema import TaskCreate, TaskOut
from ..services.TaskService import TaskService
import logging

logger = logging.getLogger(__name__)

TaskRouter = APIRouter(
    prefix="/tasks"
)

@TaskRouter.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, taskService: TaskService = Depends()):

    new_task = taskService.create_task(
        task_id=payload.task_id,
        task_name=payload.task_name,
        owner=payload.owner,
        task_group=payload.task_group,
        task_deps_id=payload.task_deps_id,
        notifications=payload.notifications,
        comment=payload.comment
        )

    return new_task

# добавить endpoint /tasks/{id}/start и POST /tasks/{id}/stop)

@TaskRouter.delete("/{task_id}")
def delete(task_id: int, taskService: TaskService = Depends()):
    task = taskService.get_task_by_id(task_id)
    check_is_none(task, task_id)
    
    if task.on_control == 'on':
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,detail=f"Can not be deleted while ON")
   
    taskService.delete(task)

    #to do добавить логи childs что parent был удален
    return task.return_id_uid()

@TaskRouter.get("/{task_id}")
def get_task_by_id(task_id: int, taskService: TaskService = Depends()):
    task = taskService.get_task_by_id(task_id)
    check_is_none(task, task_id)  
    return task

@TaskRouter.get("")
def get_tasks(taskService: TaskService = Depends()):
    return taskService.get_all()

@TaskRouter.put("/{task_id}/on")
def get_tasks(task_id: int, taskService: TaskService = Depends()):
    task = taskService.get_task_by_id(task_id)
    check_is_none(task, task_id)

    if task.on_control == 'off':
        task.on_control = 'on'
    else: 
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"You try to ON while it is already ON")
    
    taskService.update(task)

@TaskRouter.put("/{task_id}/off")
def get_tasks(task_id: int, taskService: TaskService = Depends()):
    task = taskService.get_task_by_id(task_id)
    check_is_none(task, task_id)

    if task.on_control == 'on':
        task.on_control = 'off'
    else: 
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"You try to OFF while it is already OFF")
    
    taskService.update(task)

@TaskRouter.put("/{task_id}")
def update_task(task_id: int, data: dict, taskService: TaskService = Depends()):
    task = taskService.get_task_by_id(task_id)
    check_is_none(task, task_id)

    old_control = task.on_control
    new_control = data.get('control')

    if new_control == 'off' and old_control == 'on':
        task.status = TaskStatusEnum.NOT_ACTIVE.value
        if task.task_deps_id is None:
            task.in_running = InRunningEnum.TO_CLEAN.value
    elif new_control == 'on' and old_control == 'off':
        task.status = TaskStatusEnum.ACTIVE.value

    for key, value in data.items():
        if hasattr(task, key):
            setattr(task, key, value)
    
    return taskService.update(task)

def check_is_none(object, param):
    if object is None:
        logger.warning(f"Task '{param}' not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Task '{param}' not found")
    
    if object.status == TaskStatusEnum.RUNNING:
        logger.warning(f"Task id '{object.task_id}' is running can not be updated")
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,detail=f"Task id '{object.task_id}' is running can not be updated")
