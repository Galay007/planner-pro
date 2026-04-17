from fastapi import HTTPException, APIRouter, Depends, status, Form,UploadFile,File,Path
from ..schemas.TaskPropertySchema import TaskPropertyCreate, TaskPropertyOut
from ..services.TaskPropertyService import TaskPropertyService
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging
from datetime import datetime
from typing import Optional,List,Annotated


logger = logging.getLogger(__name__)

TaskPropertyRouter = APIRouter(
    prefix="/task_properties"
)


@TaskPropertyRouter.post("", status_code=status.HTTP_201_CREATED )
def create_connection_handler(
    
    task_id: int = Form(...),
    from_dt: Optional[datetime] = Form(None),
    until_dt: Optional[datetime] = Form(None),
    connection_id: int = Form(...),
    cron_expression: Optional[str] = Form(None),
    task_type: str = Form(...),
    email: Optional[str] = Form(None),
    tg_chat_id: Optional[str] = Form(None),
    root_folder: str = Form(...),
    files: List[UploadFile] = File(...),    
    taskPropertyService: TaskPropertyService = Depends()):
    
    new_task_property = taskPropertyService.create(
        task_id=task_id,
        from_dt=from_dt,
        until_dt=until_dt,
        connection_id=connection_id,
        cron_expression=cron_expression,
        task_type=task_type,
        email=email,
        tg_chat_id=tg_chat_id,
        root_folder=root_folder,
        files=files,

    )

    return new_task_property

@TaskPropertyRouter.get("", response_model=List[TaskPropertyOut])
def get_tasks(taskPropertyService: TaskPropertyService = Depends()):

    return taskPropertyService.get_all()


@TaskPropertyRouter.get("/{task_id}", response_model=TaskPropertyOut)
def get_task_by_id(task_id: int, taskPropertyService: TaskPropertyService = Depends()):
    task_property = taskPropertyService.get_by_task_id(task_id)
    check_is_none(task_property, task_id)
    
    return task_property

@TaskPropertyRouter.put("/{task_id}")
def update_task_property(
    
    task_id: int = Path(...),
    from_dt: Optional[datetime] = Form(None),
    until_dt: Optional[datetime] = Form(None),
    connection_id: Optional[int] = Form(None),
    cron_expression: Optional[str] = Form(None),
    task_type: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    tg_chat_id: Optional[str] = Form(None),
    root_folder: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    is_manual: bool = Form(),
    manual_script: Optional[str] = Form(None),
    taskPropertyService: TaskPropertyService = Depends()
    ):
    
    print(is_manual)
    print(manual_script)
    # from pathlib import Path
    # root_folder = str(Path(root_folder).as_posix())

    if root_folder is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,detail=f"Files for task property '{task_id}' are missing")

    task_property = taskPropertyService.get_by_task_id(task_id)
    check_is_none(task_property, task_id)

    if task_property.task.on_control == "on":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Can't apply changes in propertyes of task id {task_id} while it is 'ON'")

    if task_property.task_type != task_type and (files is None or len(files) == 0):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,detail=f"No attached files for new task type '{task_type}'")
    
    if task_property.original_path != root_folder and (files is None or len(files) == 0):
       
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,detail=f"No attached files for new folder '{root_folder}'")

    data = {
        "from_dt": from_dt,
        "until_dt": until_dt,
        "connection_id": connection_id,
        "cron_expression": cron_expression,
        "original_path": str(root_folder),
        "email": email,
        "tg_chat_id": tg_chat_id
    }

    for key, value in data.items():
        if value is not None and hasattr(task_property, key):
            setattr(task_property, key, value)

    updated_task_property = taskPropertyService.update(task_property, files, root_folder, task_type)

    return updated_task_property


def check_is_none(object, param):
    if object is None:
        logger.warning(f"Property task '{param}' not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Property task '{param}' not found")
