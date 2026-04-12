from fastapi import HTTPException, APIRouter, Depends, status
from ..models.TaskModel import TaskStatusEnum, InRunningEnum
from ..schemas.TaskSchema import TaskCreate, TaskResponse
from ..services.TaskService import TaskService
from typing import List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

TaskRouter = APIRouter(
    prefix="/tasks"
)

@TaskRouter.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, taskService: TaskService = Depends()):

    if get_object_from_db(taskService, payload.task_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"Taks with id '{payload.task_id}' already exists")

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

@TaskRouter.get("/max_task_id")
def get_tasks(taskService: TaskService = Depends()):
    return taskService.get_max_task_id()

@TaskRouter.delete("/{task_id}")
def delete(task_id: int, taskService: TaskService = Depends()):
    task = get_object_from_db(taskService, task_id)
    check_is_none(task, task_id)
    check_is_running(task)
    
    if task.on_control == 'on':
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,detail=f"Can not be deleted while ON")
    taskService.delete(task)

    #to do добавить логи childs что parent был удален
    return task.return_id_uid()

@TaskRouter.get("/{task_id}")
def get_task_by_id(task_id: int, taskService: TaskService = Depends()):
    task = get_object_from_db(taskService, task_id)
    check_is_none(task, task_id)  
    return task

@TaskRouter.get("", response_model=List[TaskResponse])
def get_tasks(taskService: TaskService = Depends()):
    return taskService.get_all()

@TaskRouter.put("/on/{task_id}")
def to_on_task(task_id: int, taskService: TaskService = Depends()):
    task = get_object_from_db(taskService, task_id)
    check_is_none(task, task_id)
    check_is_running(task)

    if task.on_control == 'off':
        if task.task_name == '-' or task.owner == '-':
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"No name or owner of task")
        
        if task.task_props is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"No task properties")
        task.on_control = 'on'
        task.status = TaskStatusEnum.ACTIVE.value
        valid, message = task.check_valid_before_on_control()

        if not valid:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=message)
    else: 
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"You try to ON while it is already ON")
    
    taskService.update_with_informing(task)

@TaskRouter.put("/off/{task_id}")
def to_off_task(task_id: int, taskService: TaskService = Depends()):
    task = get_object_from_db(taskService, task_id)
    check_is_none(task, task_id)
    check_is_running(task)

    if task.on_control == 'on':    
        task.on_control = 'off'
        task.status = TaskStatusEnum.NOT_ACTIVE.value
    else: 
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"You try to OFF while it is already OFF")
    
    taskService.update_with_informing(task)

@TaskRouter.put("/run/{task_id}")
def to_run_task(task_id: int, taskService: TaskService = Depends()): 
    task = get_object_from_db(taskService, task_id)
    check_is_none(task, task_id)
    check_is_running(task)

    if datetime.now() <= task.run_expire_at:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"Task id '{task.task_id}' is one-time running, wait finish")
    
    valid, message = task.check_valid_for_manual_execute()

    if not valid:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=message)

    taskService.one_time_run(task)

@TaskRouter.put("/{task_id}")
def update_task(task_id: int, data: dict, taskService: TaskService = Depends()):
    task = get_object_from_db(taskService, task_id)
    check_is_none(task, task_id)
    check_is_running(task)

    for key, value in data.items():
        if hasattr(task, key):
            setattr(task, key, value)
    
    return taskService.update_with_informing(task)

def get_object_from_db(service, param):
    return service.get_task_by_id(param)

def check_is_none(object, param):
    if object is None:
        logger.warning(f"Task '{param}' not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Task '{param}' not found")
    
def check_is_running(object):
    if object.status == TaskStatusEnum.RUNNING:
        logger.warning(f"Task id '{object.task_id}' is running, wait finish")
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,detail=f"Task id '{object.task_id}' is running, wait finish")
