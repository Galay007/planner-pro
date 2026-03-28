from contextlib import contextmanager
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from .Config import settings
from sqlalchemy import text
import time


Base = declarative_base()

engine = create_engine(
    settings.database_url,
    future=True,
    pool_recycle=300,          
    pool_timeout=10,           
    pool_size=10,              
    max_overflow=10,           
    echo=False,   
    pool_pre_ping=True         
)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)
# db_session = scoped_session(SessionLocal)

db_session = SessionLocal()

# @contextmanager
# def get_connection():
#     with engine.begin() as connection:
#         print(f"🟢 Gave connection")
#         yield connection


def get_orm_connection():

    try:
        print(f"🟢 Given db connection from pool")
        yield db_session
        db_session.commit()
    except Exception as e:
        print(f"🚨 DB ROLLBACK: {type(e).__name__}")
        print({str(e).split('\n')[0]})
        db_session.rollback()
        raise
    finally:
        print("🔒 Connection from pool to DB removed")
        db_session.close()

def init_metadata_db():
    db_ok = check_db_connection()
    if db_ok:
        try:
            Base.metadata.create_all(bind=engine)
            for table in Base.metadata.sorted_tables:
                print(f"  - {table.name}")

            print("Таблицы созданы")
        except Exception as e:
            print(f"Ошибка создания таблиц: {e}")
    
def check_db_connection(max_retries=3, delay=2):

    print('checking db connection')
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("БД доступна")
            return True
        except Exception as e:
            print(f"Попытка {attempt+1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    print("БД недоступна")
    return False

#     /*CREATE TABLE connections (
#     id SERIAL PRIMARY KEY,
#     name VARCHAR(100) NOT NULL,
#     conn_type VARCHAR(50) NOT NULL,
#     host VARCHAR(255) NOT NULL,
#     port INT4,
#     db_name VARCHAR(255),
#     login VARCHAR(100),
#     password VARCHAR(255),
#     dp_path TEXT NULL,
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# );*/


# --CREATE INDEX IF NOT EXISTS idx_task_properties_task_id ON task_properties(task_id);