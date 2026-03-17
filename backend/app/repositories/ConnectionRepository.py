from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from fastapi import Depends
from sqlalchemy.orm import Session, lazyload

from ..configs.Database import get_orm_connection
from ..models.ConnectionModel import Connection


class ConnectionRepository:
    db: Session

    def __init__(
        self, db: Session = Depends(get_orm_connection)
    ) -> None:
        self.db = db

    def list(
        self,
        name: Optional[str],
        limit: Optional[int],
        start: Optional[int]
    ) -> List[Connection]:
        query = self.db.query(Connection)

        if name:
            query = query.filter_by(name=name)

        return query.offset(start).limit(limit).all()

    def get(self, name: str) -> Connection:      
        return self.db.query(Connection).filter(Connection.name == name).first()

    def create(self, connection: Connection) -> Connection:
        self.db.add(connection)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ValueError(f"Connection with name '{connection.name}' already exists")

        self.db.refresh(connection)
        return connection

    def update(self, id: int, connection: Connection) -> Connection:
        connection.id = id
        self.db.merge(connection)
        self.db.commit()
        return connection

    def delete(self, connection: Connection) -> None:
        self.db.delete(connection)
        self.db.commit()
        self.db.flush()