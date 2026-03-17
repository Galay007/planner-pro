from fastapi import Depends
from ..repositories.ConnectionRepository import ConnectionRepository
from ..models.ConnectionModel import Connection

class ConnectionService:
    connectionRepository: ConnectionRepository

    def __init__(
        self, connectionRepository: ConnectionRepository = Depends()
    ) -> None:
        self.connectionRepository = connectionRepository

    def create_connection(self,
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
        new_connection.password = password  # setter сам зашифрует

        return self.connectionRepository.create(new_connection)


    def get_connection_by_name(self,name: str) -> Connection | None:
                 
        return self.connectionRepository.get(name)
