from typing import Optional
from sqlalchemy import (Column, Integer, String, Text,DateTime, text, func)
import logging
from cryptography.fernet import Fernet
from ..configs.Config import settings
from ..configs.Database import Base
from ..utils.DatetimeUtils import DateTimeUtils
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

logger = logging.getLogger(__name__)

FERNET_KEY = settings.fernet_key
fernet = Fernet(FERNET_KEY.encode() if isinstance(FERNET_KEY, str) else FERNET_KEY)

DB_DRIVERS = {
    'postgresql': 'psycopg',
    'mysql': 'pymysql',
    'mariadb': 'mariadb',
    'mssql': 'pyodbc',
    'oracle': 'oracledb',
    'sqlite': None,
    'teradata': 'teradatasql'
}

class Connection(Base):
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)          
    conn_type = Column(String(50), nullable=False)                   
    host = Column(String(255), nullable=True)
    port = Column(Integer, nullable=True)
    db_name = Column(String(255), nullable=True)                      
    login = Column(String(255), nullable=True)
    pass_str = Column(Text, nullable=True)    
    db_path = Column(Text,nullable=True)    
    created_at = Column(DateTime(timezone=False),default=DateTimeUtils.local_wo_microsec)   


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

    def build_sqlalchemy_url(self, driver: Optional[str] = None) -> str:
        if self.conn_type == 'sqlite':
            try:
                db_path = Path(self.db_path).resolve()
                if db_path.exists() and db_path.is_file():
                    return f"{self.conn_type}:///{db_path.as_posix()}"
            except Exception as e:
                logger.exception(f"Wrong path to sqlite {e}")
                return None
        
        default_driver  = DB_DRIVERS[self.conn_type]   
        selected_driver = driver or default_driver

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
        
        return f"{self.conn_type}+{selected_driver}://{auth}{self.host}{port_part}{schema_part}"
    
    def test_db_connection(self, driver: Optional[str] = None) -> bool:
        url = self.build_sqlalchemy_url(driver)

        engine = None
        try:
            engine = create_engine(url, echo=False)
            LocalSession = sessionmaker(bind=engine)
            with LocalSession.begin() as conn:
                result = conn.execute(text("SELECT 1;"))
                result.fetchone()
            return True
        except Exception as e:
            logger.exception(f"Connection exception {e}", exc_info=False)
            return False
        finally:
            if engine:
                engine.dispose()

    def normalize(self):
 
        return {
            "id": self.id.__str__(),
            "name": self.name.__str__(),
            "conn_type": self.conn_type.__str__(),                 
            "host": self.host.__str__(),      
            "port": self.port.__str__(),      
            "db_name": self.db_name.__str__(),                           
            "login": self.login.__str__(),            
            "db_path": self.db_path.__str__(),
            "created_at": self.created_at.__str__()   
        }

