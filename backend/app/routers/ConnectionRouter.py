from fastapi import HTTPException, APIRouter, Depends, status
from ..schemas.ConnectionSchema import ConnectionCreate, ConnectionOut
from ..services.ConnectionService import ConnectionService
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

ConnectionRouter = APIRouter(
    prefix="/connections"
)


@ConnectionRouter.post("", response_model=ConnectionCreate, status_code=status.HTTP_201_CREATED)
def create_connection_handler(payload: ConnectionOut, connectionService: ConnectionService = Depends()):

    if get_object_from_db(connectionService, payload.name):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"Connection '{payload.name}' already exists")

    new_connection = connectionService.create(
        name=payload.name,
        conn_type=payload.conn_type,
        host=payload.host,
        port=payload.port,
        db_name=payload.db_name,
        login=payload.login,
        password=payload.pass_str,
        db_path=payload.db_path
    )

    connection = connectionService.get_by_name(new_connection.name)

    return connection


@ConnectionRouter.get("/{name}", response_model=ConnectionOut)
def get_connection_handler(name: str, connectionService: ConnectionService = Depends()):
    connection = get_object_from_db(connectionService, name)
    check_is_none(connection, name)
    
    return connection

@ConnectionRouter.delete("/{name}")
def delete(name: str, connectionService: ConnectionService = Depends()):
    connection = get_object_from_db(connectionService, name)
    check_is_none(connection, name)
    
    return connectionService.delete(connection)

@ConnectionRouter.get("")
def get_tasks(connectionService: ConnectionService = Depends()):
    return connectionService.get_all()

def get_object_from_db(service, param):
    return service.get_by_name(param)

def check_is_none(object, param):
    if object is None:
        logger.warning(f"Connection task '{param}' not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Connection task '{param}' not found")
