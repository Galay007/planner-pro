from fastapi import HTTPException, APIRouter, Depends, status, Form, UploadFile, File, Path
from ..schemas.TaskPropertySchema import TaskPropertyCreate, TaskPropertyOut, TaskPropertyIn
from ..services.TaskPropertyService import TaskPropertyService
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging
from datetime import datetime
from typing import Optional, List
from io import BytesIO


logger = logging.getLogger(__name__)

TaskPropertyRouter = APIRouter(
    prefix="/task_properties"
)

def task_property_form(
    task_type: str = Form(...),
    is_manual: Optional[bool] = Form(None),
    from_dt: Optional[datetime] = Form(None),
    until_dt: Optional[datetime] = Form(None),
    connection_id: Optional[int] = Form(None),
    cron_expression: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    tg_chat_id: Optional[str] = Form(None),
    root_folder: Optional[str] = Form(None),
    manual_script: Optional[str] = Form(None),
) -> TaskPropertyIn:
    return TaskPropertyIn(
        task_type=task_type,
        is_manual=is_manual,
        from_dt=from_dt,
        until_dt=until_dt,
        connection_id=connection_id,
        cron_expression=cron_expression,
        email=email,
        tg_chat_id=tg_chat_id,
        root_folder=root_folder,
        manual_script=manual_script,
    )

@TaskPropertyRouter.post("", status_code=status.HTTP_201_CREATED, response_model=TaskPropertyOut )
def create_connection_handler(
    
    task_id: int = Form(...),
    form: TaskPropertyIn = Depends(task_property_form),  
    files: Optional[List[UploadFile]] = File(None),
    taskPropertyService: TaskPropertyService = Depends()
    ):

    if form.is_manual is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,detail=f"Create or attach new files")
    
    if form.connection_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,detail=f"Choose connection name")
    
    new_task_property = taskPropertyService.create(
        task_id=task_id,
        from_dt=form.from_dt,
        until_dt=form.until_dt,
        connection_id=form.connection_id,
        cron_expression=form.cron_expression,
        task_type=form.task_type,
        email=form.email,
        tg_chat_id=form.tg_chat_id,
        root_folder=form.root_folder,
        files=files,
    )

    if files is None:
        files = []

    do_validation(form, task_id, files)

    return new_task_property

@TaskPropertyRouter.get("", response_model=List[TaskPropertyOut])
def get_tasks(taskPropertyService: TaskPropertyService = Depends()):

    return taskPropertyService.get_all()


@TaskPropertyRouter.get("/{task_id}", response_model=TaskPropertyOut)
def get_task_by_id(task_id: int, taskPropertyService: TaskPropertyService = Depends()):
    task_property = taskPropertyService.get_by_task_id(task_id)
    check_is_none(task_property, task_id)
    
    return task_property

@TaskPropertyRouter.put("/{task_id}", response_model=TaskPropertyOut)
def update_task_property(
    task_id: int = Path(...),
    form: TaskPropertyIn = Depends(task_property_form),
    files: Optional[List[UploadFile]] = File(None),
    taskPropertyService: TaskPropertyService = Depends()
    ):
    
    if form.connection_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,detail=f"Choose connection name")

    if form.is_manual is not None:
        if files is None:
            files = []

        do_validation(form, task_id, files)

    task_property = taskPropertyService.get_by_task_id(task_id)
    check_is_none(task_property, task_id)

    if task_property.task_type != form.task_type and form.is_manual is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,detail=f"Task type has been changed. Please update script files")

    data = {
        "from_dt": form.from_dt,
        "until_dt": form.until_dt,
        "connection_id": form.connection_id,
        "cron_expression": form.cron_expression,
        "email": form.email,
        "tg_chat_id": form.tg_chat_id
    }

    for key, value in data.items():
        if value is not None and hasattr(task_property, key):
            setattr(task_property, key, value)

    updated_task_property = taskPropertyService.update(task_property, files, form.root_folder, form.task_type, form.is_manual)

    return updated_task_property


def check_is_none(object, param):
    if object is None:
        logger.warning(f"Property task '{param}' not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Property task '{param}' not found")
    
def do_validation(form: TaskPropertyIn, task_id: int, files):
    if form.root_folder is None and form.is_manual == False:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,detail=f"Folder path for '{task_id}' is missing")

    if len(files) == 0 and form.is_manual == False:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,detail=f"New files for '{task_id}' not selected")

    if form.is_manual:
        form.root_folder = str(task_id)

        new_file = UploadFile(
            filename=f"custom.{form.task_type}",
            file=BytesIO(form.manual_script.encode("utf-8")),
        )
        files.clear()
        files.append(new_file)
        
