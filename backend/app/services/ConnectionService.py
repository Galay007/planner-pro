from fastapi import Depends
from ..repositories.ConnectionRepositoryAPI import ConnectionRepositoryAPI
from ..models.ConnectionModel import Connection
from .TaskRunningService import TaskRunningService
from typing import List, Optional
from .SseService import send_to_client_update
import logging

logger = logging.getLogger(__name__)

class ConnectionService:
    connectionRepositoryAPI: ConnectionRepositoryAPI
    taskRunningService: TaskRunningService


    def __init__(
        self, connectionRepositoryAPI: ConnectionRepositoryAPI = Depends()
    ) -> None:
        self.connectionRepositoryAPI = connectionRepositoryAPI
        self.taskRunningService = TaskRunningService(self.connectionRepositoryAPI.get_db())

    def create(self,
        name: str,
        conn_type: str,
        host: Optional[str],
        port: Optional[int],
        db_name: Optional[str],
        login: Optional[str],
        password: Optional[str],
        db_path: Optional[str]
        ) -> Connection:
        
        new_connection = Connection(
            name=name,
            conn_type=conn_type,
            host=host,
            port=port,
            db_name=db_name,
            login=login,
            db_path=db_path
        )
        new_connection.password = password  # setter сам зашифрует пароль

        return self.connectionRepositoryAPI.create(new_connection)


    def get_by_name(self,name: str) -> Optional[Connection]:
                 
        return self.connectionRepositoryAPI.get(name)
    
    def delete(self,connection: Connection) -> None:
        self.connectionRepositoryAPI.delete(connection)
        self.taskRunningService.refresh_runnings()
        send_to_client_update(event_type="task_update")

    def get_all(self) -> List[Connection]:
        return self.connectionRepositoryAPI.get_all()
    
    def test_existing_connection(self, test_connection: Connection):
        return test_connection.test_db_connection()


    def test_new_connection(self,
        name: str,
        conn_type: str,
        host: Optional[str],
        port: Optional[int],
        db_name: Optional[str],
        login: Optional[str],
        password: Optional[str],
        db_path: Optional[str]
        ) -> Connection:
        
        test_connection = Connection(
            name=name,
            conn_type=conn_type,
            host=host,
            port=port,
            db_name=db_name,
            login=login,
            db_path=db_path
        )
        test_connection.password = password  # setter сам зашифрует пароль

        return test_connection.test_db_connection()

    

