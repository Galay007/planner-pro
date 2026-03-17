from contextlib import contextmanager
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from .Config import settings


Base = declarative_base()
engine = create_engine(settings.database_url, future=True, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


@contextmanager
def get_connection():
    with engine.begin() as connection:
        yield connection


def get_orm_connection():
    db = scoped_session(SessionLocal)
    try:
        yield db
    finally:
        db.close()


MIGRATION_SQL = """


CREATE TABLE IF NOT EXISTS task_properties (
    task_uid BIGINT PRIMARY KEY REFERENCES tasks(task_uid) ON DELETE CASCADE,
    task_id BIGINT NOT NULL,
    launch_day TEXT NOT NULL,
    launch_time TEXT NOT NULL,
    end_day TEXT NOT NULL,
    end_time TEXT NOT NULL,
    file_type TEXT NOT NULL DEFAULT 'SQL' CHECK (file_type IN ('SQL', 'PY', 'BAT')),
    connection TEXT NOT NULL,
    notification_channel TEXT NOT NULL,
    notification_value TEXT NOT NULL,
    cron_expression TEXT NOT NULL
);


"""


def run_migrations() -> None:
    with get_connection() as connection:
        connection.exec_driver_sql(MIGRATION_SQL)

def init_metadata_db():
    Base.metadata.create_all(bind=engine)


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