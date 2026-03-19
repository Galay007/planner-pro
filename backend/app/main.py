import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from .routers.ConnectionRouter import ConnectionRouter
from .routers.TaskRouter import TaskRouter
from .routers.TaskHistRouter import TaskHistRouter
from .configs.Config import settings
from .configs.Database import get_connection, run_migrations, init_metadata_db
from .schemas55 import Task, TaskCreate, TaskPropertiesBase, TaskPropertiesRecord, TaskReplace
from .exceptions import register_db_exception_handlers

# from sqlalchemy.ext.asyncio import AsyncSession, create_engine  # для ассинхронных запросов
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker

logging.basicConfig(
    level=logging.WARNING,  # Минимальный уровень (INFO, DEBUG, WARNING, ERROR)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)

@asynccontextmanager
async def lifespan(_: FastAPI):
    run_migrations()
    yield



init_metadata_db()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
register_db_exception_handlers(app)

app.include_router(ConnectionRouter)
app.include_router(TaskRouter)
app.include_router(TaskHistRouter)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",  
        "http://127.0.0.1:8080",
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)



def _to_task_properties_record(row: dict) -> TaskPropertiesRecord:
    return TaskPropertiesRecord(
        id=int(row["id"]),
        task_id=int(row["task_id"]),
        launch_day=row["launch_day"],
        launch_time=row["launch_time"],
        end_day=row["end_day"],
        end_time=row["end_time"],
        file_type=row["file_type"],
        connection=row["connection"],
        notification_channel=row["notification_channel"],
        notification_value=row["notification_value"],
        cronExpression=row["cron_expression"],
    )





@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}








@app.get("/properties/{task_id}", response_model=TaskPropertiesRecord)
def get_task_properties(task_id: int) -> TaskPropertiesRecord:
    with get_connection() as connection:
        row = connection.execute(
            text(
                """
                SELECT id, task_id, launch_day, launch_time, end_day, end_time,
                       file_type, connection, notification_channel, notification_value, cron_expression
                FROM task_properties
                WHERE task_id = :task_id
                """
            ),
            {"task_id": task_id},
        ).mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail="Task properties not found")

    return _to_task_properties_record(row)


@app.post("/properties/{task_id}", response_model=TaskPropertiesRecord, status_code=201)
@app.put("/properties/{task_id}", response_model=TaskPropertiesRecord)
def upsert_task_properties(task_id: int, payload: TaskPropertiesBase) -> TaskPropertiesRecord:
    with get_connection() as connection:
        exists = connection.execute(text("SELECT 1 FROM tasks WHERE id = :id"), {"id": task_id}).first()
        if exists is None:
            raise HTTPException(status_code=404, detail="Task not found")

        row = connection.execute(
            text(
                """
                INSERT INTO task_properties (
                    task_id, launch_day, launch_time, end_day, end_time,
                    file_type, connection, notification_channel, notification_value, cron_expression
                )
                VALUES (
                    :task_id, :launch_day, :launch_time, :end_day, :end_time,
                    :file_type, :connection, :notification_channel, :notification_value, :cron_expression
                )
                ON CONFLICT (task_id)
                DO UPDATE SET
                    launch_day = EXCLUDED.launch_day,
                    launch_time = EXCLUDED.launch_time,
                    end_day = EXCLUDED.end_day,
                    end_time = EXCLUDED.end_time,
                    file_type = EXCLUDED.file_type,
                    connection = EXCLUDED.connection,
                    notification_channel = EXCLUDED.notification_channel,
                    notification_value = EXCLUDED.notification_value,
                    cron_expression = EXCLUDED.cron_expression
                RETURNING id, task_id, launch_day, launch_time, end_day, end_time,
                          file_type, connection, notification_channel, notification_value, cron_expression
                """
            ),
            {
                "task_id": task_id,
                "launch_day": payload.launch_day,
                "launch_time": payload.launch_time,
                "end_day": payload.end_day,
                "end_time": payload.end_time,
                "file_type": payload.file_type,
                "connection": payload.connection,
                "notification_channel": payload.notification_channel,
                "notification_value": payload.notification_value,
                "cron_expression": payload.cronExpression,
            },
        ).mappings().one()

    return _to_task_properties_record(row)


@app.delete("/properties/{task_id}", status_code=204)
def delete_task_properties(task_id: int) -> None:
    with get_connection() as connection:
        deleted = connection.execute(
            text("DELETE FROM task_properties WHERE task_id = :task_id"),
            {"task_id": task_id},
        )
    if deleted.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task properties not found")
    

