from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, create_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker
from cryptography.fernet import Fernet
from ..configs.Config import settings

Base = declarative_base()

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
    password_encrypted = Column(Text, nullable=True)    
    db_path = Column(Text,nullable=True)             


    @property
    def password(self) -> str | None:
        """Вернёт расшифрованный пароль (или None)."""
        if not self.password_encrypted:
            return None
        # храним как base64-строку, шифруем/расшифровываем байты
        return fernet.decrypt(self.password_encrypted.encode()).decode()

    @password.setter
    def password(self, value: str | None) -> None:
        """При присвоении шифруем и кладём в password_encrypted."""
        if value is None or value == "":
            self.password_encrypted = None
        else:
            token = fernet.encrypt(value.encode())
            self.password_encrypted = token.decode()

    def build_sqlalchemy_url(self) -> str:
        """
        Собрать DSN, например:
        postgresql+psycopg2://user:pass@host:5432/dbname
        """
        login = self.login or ""
        password = self.password or ""
        auth = ""
        if login:
            if password:
                auth = f"{login}:{password}@"
            else:
                auth = f"{login}@"

        port_part = f":{self.port}" if self.port else ""
        schema_part = f"/{self.schema}" if self.schema else ""
        return f"{self.conn_type}://{auth}{self.host}{port_part}{schema_part}"
    
    def normalize(self):
        return {
            "id": self.id.__str__(),
            "name": self.name.__str__(),
        }

    def encrypt_secret(value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        token = fernet.encrypt(value.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt_secret(token: Optional[str]) -> Optional[str]:
        if not token:
            return None
        return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
