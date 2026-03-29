from fastapi import Depends
from ..repositories.ConnectionRepositoryAPI import ConnectionRepositoryAPI
from ..models.ConnectionModel import Connection
from typing import List

class ConnectionService:
    connectionRepositoryAPI: ConnectionRepositoryAPI

    def __init__(
        self, connectionRepositoryAPI: ConnectionRepositoryAPI = Depends()
    ) -> None:
        self.connectionRepositoryAPI = connectionRepositoryAPI

    def create(self,
        name: str,
        conn_type: str,
        host: str,
        port: int | None,
        db_name: str | None,
        login: str | None,
        password: str | None,
        db_path: str | None
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


    def get_by_name(self,name: str) -> Connection | None:
                 
        return self.connectionRepositoryAPI.get(name)
    
    def delete(self,connection: Connection) -> None:
        return self.connectionRepositoryAPI.delete(connection)
    
    def get_all(self) -> List[Connection]:
        return self.connectionRepositoryAPI.get_all()
