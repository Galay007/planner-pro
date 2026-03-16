from fastapi import HTTPException, APIRouter, Depends, status
from ..schemas.ConnectionSchema import ConnectionCreate, ConnectionOut
from ..services.ConnectionService import ConnectionService


ConnectionRouter = APIRouter(
    prefix="/connections"
)


@ConnectionRouter.post("/", response_model=ConnectionOut, status_code=status.HTTP_201_CREATED)
def create_connection_handler(payload: ConnectionCreate, connectionService: ConnectionService = Depends()):
    try:
        new_id = connectionService.create_connection(
            name=payload.name,
            conn_type=payload.conn_type,
            host=payload.host,
            port=payload.port,
            db_name=payload.db_name,
            login=payload.login,
            password=payload.password,
            db_path=payload.db_path
        )
    except ValueError as e:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not new_id:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Connection was not created")

    return new_id


@ConnectionRouter.get("/{name}", response_model=ConnectionOut)
def get_connection_handler(name: str, connectionService: ConnectionService = Depends()):
    return connectionService.get(name)


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