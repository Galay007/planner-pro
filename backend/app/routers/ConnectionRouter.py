from fastapi import HTTPException, APIRouter, Depends, status
from ..schemas.ConnectionSchema import ConnectionCreate, ConnectionOut
from ..services.ConnectionService import ConnectionService
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

ConnectionRouter = APIRouter(
    prefix="/connections"
)


@ConnectionRouter.post("", response_model=ConnectionOut, status_code=status.HTTP_201_CREATED)
def create_connection_handler(payload: ConnectionCreate, connectionService: ConnectionService = Depends()):
    
    new_connection = connectionService.create_connection(
        name=payload.name,
        conn_type=payload.conn_type,
        host=payload.host,
        port=payload.port,
        db_name=payload.db_name,
        login=payload.login,
        password=payload.password,
        db_path=payload.db_path
    )

    connection = connectionService.get_by_name(new_connection.name)

    return connection.normalize()


@ConnectionRouter.get("/{name}")
def get_connection_handler(name: str, connectionService: ConnectionService = Depends()):
    connection = connectionService.get_by_name(name)
    check_is_none(connection)
    
    return connection.build_sqlalchemy_url()

@ConnectionRouter.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete(name: str, connectionService: ConnectionService = Depends()):
    connection = connectionService.get_by_name(name)
    check_is_none(connection)
    
    return connectionService.delete(connection)

@ConnectionRouter.get("")
def get_tasks(connectionService: ConnectionService = Depends()):

    return connectionService.get_all()

def check_is_none(param):
    if param is None:
        logger.warning(f"Connection task '{param}' not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Connection task '{param}' not found")
