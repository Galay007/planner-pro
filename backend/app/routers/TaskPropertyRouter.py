from fastapi import HTTPException, APIRouter, Depends, status, Form,UploadFile,File
from ..schemas.TaskProperty import TaskPropertyCreate
from ..services.TaskPropertyService import TaskPropertyService
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging
from datetime import datetime
from typing import Optional,List

logger = logging.getLogger(__name__)

TaskPropertyRouter = APIRouter(
    prefix="/task_properties"
)


@TaskPropertyRouter.post("", status_code=status.HTTP_201_CREATED )
def create_connection_handler(
    
    task_id: int = Form(...),
    from_dt: datetime = Form(...),
    until_dt: datetime = Form(...),
    connection_id: int = Form(...),
    cron_expression: Optional[str] = Form(None),
    task_type: str = Form(...),
    email: Optional[str] = Form(None),
    tg_chat_id: Optional[str] = Form(None),
    root_folder: str = Form(...),
    files: List[UploadFile] = File(...),    
    propertyService: TaskPropertyService = Depends()):
    
    new_task_property = propertyService.create(
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

# @TaskPropertyRouter.post("", )
# def create_connection_handler(payload: TaskPropertyCreate, propertyService: TaskPropertyService = Depends()):
    
#     new_task_property = propertyService.create(
#         from_dt=payload.from_dt,
#         until_dt=payload.until_dt,
#         connection_id=payload.connection_id,
#         cron_expression=payload.cron_expression,
#         task_type=payload.task_type,
#         email=payload.email,
#         tg_chat_id=payload.tg_chat_id,
#         root_folder=payload.root_folder,
#         files=payload.files,

#     )

#     return new_task_property


# @ConnectionRouter.get("/{name}")
# def get_connection_handler(name: str, connectionService: ConnectionService = Depends()):
#     connection = connectionService.get_by_name(name)
#     check_is_none(connection)
    
#     return connection.build_sqlalchemy_url()

# @ConnectionRouter.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
# def delete(name: str, connectionService: ConnectionService = Depends()):
#     connection = connectionService.get_by_name(name)
#     check_is_none(connection)
    
#     return connectionService.delete(connection)

# @ConnectionRouter.get("")
# def get_tasks(connectionService: ConnectionService = Depends()):

#     return connectionService.get_all()

# def check_is_none(param):
#     if param is None:
#         logger.warning(f"Connection task '{param}' not found")
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Connection task '{param}' not found")
