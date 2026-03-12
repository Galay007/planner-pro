from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from .config import settings
from .db import get_connection, run_migrations
from .schemas import Task, TaskCreate, TaskPropertiesBase, TaskPropertiesRecord, TaskReplace


@asynccontextmanager
async def lifespan(_: FastAPI):
    run_migrations()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
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


def _task_from_row(row: dict) -> Task:
    return Task(
        id=int(row["id"]),
        name=row["name"],
        group=row["task_group"],
        employee=row["employee"],
        control=row["control"],
        dependency=row["dependency"],
        status=row["status"],
        notifications=row["notifications"],
        logs=row["logs"],
        comment=row["comment"],
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tasks", response_model=list[Task])
def list_tasks() -> list[Task]:
    with get_connection() as connection:
        rows = connection.execute(text("SELECT * FROM tasks ORDER BY id ASC")).mappings().all()
    return [_task_from_row(row) for row in rows]


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int) -> Task:
    with get_connection() as connection:
        row = connection.execute(
            text("SELECT * FROM tasks WHERE id = :id"), {"id": task_id}
        ).mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return _task_from_row(row)


@app.post("/tasks/{task_id}", response_model=Task, status_code=201)
def create_task(task_id: int, payload: TaskCreate) -> Task:
    if payload.id != task_id:
        raise HTTPException(status_code=400, detail="Path task_id must match payload id")

    try:
        with get_connection() as connection:
            row = connection.execute(
                text(
                    """
                    INSERT INTO tasks (id, name, task_group, employee, control, dependency, status, notifications, logs, comment)
                    VALUES (:id, :name, :task_group, :employee, :control, :dependency, :status, :notifications, :logs, :comment)
                    RETURNING *
                    """
                ),
                {
                    "id": payload.id,
                    "name": payload.name,
                    "task_group": payload.group,
                    "employee": payload.employee,
                    "control": payload.control,
                    "dependency": payload.dependency,
                    "status": payload.status,
                    "notifications": payload.notifications,
                    "logs": payload.logs,
                    "comment": payload.comment,
                },
            ).mappings().one()
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Task with this id already exists or dependency is invalid") from exc

    return _task_from_row(row)


@app.put("/tasks/{task_id}", response_model=Task)
def replace_task(task_id: int, payload: TaskReplace) -> Task:
    with get_connection() as connection:
        row = connection.execute(
            text(
                """
                UPDATE tasks
                SET name = :name,
                    task_group = :task_group,
                    employee = :employee,
                    control = :control,
                    dependency = :dependency,
                    status = :status,
                    notifications = :notifications,
                    logs = :logs,
                    comment = :comment
                WHERE id = :id
                RETURNING *
                """
            ),
            {
                "id": task_id,
                "name": payload.name,
                "task_group": payload.group,
                "employee": payload.employee,
                "control": payload.control,
                "dependency": payload.dependency,
                "status": payload.status,
                "notifications": payload.notifications,
                "logs": payload.logs,
                "comment": payload.comment,
            },
        ).mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return _task_from_row(row)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int) -> None:
    with get_connection() as connection:
        deleted = connection.execute(
            text("DELETE FROM tasks WHERE id = :id"), {"id": task_id}
        )
    if deleted.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found")


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
