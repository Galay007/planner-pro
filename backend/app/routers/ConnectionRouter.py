from fastapi import HTTPException, APIRouter, Depends, status
from ..schemas.ConnectionSchema import ConnectionSchem
from ..services.ConnectionService import ConnectionService
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

ConnectionRouter = APIRouter(
    prefix="/connections"
)


@ConnectionRouter.post("", status_code=status.HTTP_201_CREATED)
def create_connection_handler(payload: ConnectionSchem, connectionService: ConnectionService = Depends()):

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


@ConnectionRouter.post("/test", status_code=status.HTTP_200_OK)
def test_connection(payload: ConnectionSchem, connectionService: ConnectionService = Depends()):
    result: bool
    test_connection = get_object_from_db(connectionService, payload.name)
    
    if test_connection is not None:
        result = connectionService.test_existing_connection(test_connection)
    else:
        result = connectionService.test_new_connection(
        name=payload.name,
        conn_type=payload.conn_type,
        host=payload.host,
        port=payload.port,
        db_name=payload.db_name,
        login=payload.login,
        password=payload.pass_str,
        db_path=payload.db_path
        )
    
    if not result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Test connection failed")


@ConnectionRouter.get("/{name}", response_model=ConnectionSchem)
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
