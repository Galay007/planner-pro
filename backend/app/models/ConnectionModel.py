from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text
)
from cryptography.fernet import Fernet
from ..configs.Config import settings
from ..configs.Database import Base


FERNET_KEY = settings.fernet_key
fernet = Fernet(FERNET_KEY.encode() if isinstance(FERNET_KEY, str) else FERNET_KEY)


class Connection(Base):
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)          
    conn_type = Column(String(50), nullable=False)                   
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=True)
    db_name = Column(String(255), nullable=True)                      
    login = Column(String(255), nullable=True)
    pass_str = Column(Text, nullable=True)    
    db_path = Column(Text,nullable=True)             


    @property
    def password(self) -> str | None:
        if not self.pass_str:
            return None
        return fernet.decrypt(self.pass_str.encode("utf-8")).decode("utf-8")

    @password.setter
    def password(self, value: str | None) -> None:
        if value is None or value == "":
            self.pass_str = None
        else:
            token = fernet.encrypt(value.encode("utf-8"))
            self.pass_str = token.decode("utf-8")

    def build_sqlalchemy_url(self) -> str:

        login = self.login or ""
        password = self.password or ""
        auth = ""
        if login:
            if password:
                auth = f"{login}:{password}@"
            else:
                auth = f"{login}@"

        port_part = f":{self.port}" if self.port else ""
        schema_part = f"/{self.db_name}" if self.db_name else ""
        return f"{self.conn_type}://{auth}{self.host}{port_part}{schema_part}"
    
    def normalize(self):
        if self.password:
            has_password = "true"
        return {
            "id": self.id.__str__(),
            "name": self.name.__str__(),
            "conn_type": self.conn_type.__str__(),                 
            "host": self.host.__str__(),      
            "port": self.port.__str__(),      
            "db_name": self.db_name.__str__(),                           
            "login": self.login.__str__(),      
            "has_password": has_password.__str__(),        
            "db_path": self.db_path.__str__(),       
        }

