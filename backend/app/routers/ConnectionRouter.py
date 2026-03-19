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
    try:
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

    # except IntegrityError as e:
    #     logger.error(f"Integrity error for connection '{payload.name}': {e}")
    #     raise HTTPException(
    #         status_code=status.HTTP_409_CONFLICT, 
    #         detail=f"Connection with name '{payload.name}' already exists"
    #     )


    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Database service unavailable"
        )

    return new_connection.normalize()


@ConnectionRouter.get("/{name}")
def get_connection_handler(name: str, connectionService: ConnectionService = Depends()):
    connection = connectionService.get_connection_by_name(name)
    
    if connection is None:
        logger.warning(f"Connection '{name}' not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Connection '{name}' not found")
    
    return connection.build_sqlalchemy_url()

@ConnectionRouter.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete(name: str, connectionService: ConnectionService = Depends()
):
    connection = connectionService.get_connection_by_name(name)
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Connection '{name}' not found")
    
    return connectionService.delete(connection)

# POST /connections
# Content-Type: application/json

# {
#   "name": "pg_local",
#   "conn_type": "postgresql",
#   "host": "localhost",
#   "port": 5432,
#   "schema_name": "mydb",
#   "login": "user",
#   "password": "secret_pwd",
#   "path_db": ""
# }