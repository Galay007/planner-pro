from fastapi import HTTPException, APIRouter, Depends, status
from ..schemas.TaskSchema import TaskCreate, TaskOut
from ..services.TaskService import TaskService


TaskRouter = APIRouter(
    prefix="/tasks"
)

# @app.get("/tasks", response_model=list[Task])
# def list_tasks() -> list[Task]:
#     with get_connection() as connection:
#         rows = connection.execute(text("SELECT * FROM tasks ORDER BY id ASC")).mappings().all()
#     return [_task_from_row(row) for row in rows]


# @app.get("/tasks/{task_id}", response_model=Task)
# def get_task(task_id: int) -> Task:
#     with get_connection() as connection:
#         row = connection.execute(
#             text("SELECT * FROM tasks WHERE id = :id"), {"id": task_id}
#         ).mappings().first()

#     if row is None:
#         raise HTTPException(status_code=404, detail="Task not found")

#     return _task_from_row(row)

# @app.delete("/tasks/{task_id}", status_code=204)
# def delete_task(task_id: int) -> None:
#     with get_connection() as connection:
#         deleted = connection.execute(
#             text("DELETE FROM tasks WHERE id = :id"), {"id": task_id}
#         )
#     if deleted.rowcount == 0:
#         raise HTTPException(status_code=404, detail="Task not found")


@TaskRouter.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, taskService: TaskService = Depends()):
    try:
        new_task = taskService.create_task(
            task_id=payload.task_id,
            control=payload.control,
            owner=payload.owner,
            task_group=payload.task_group,
            task_deps_id=payload.task_deps_id,
            task_deps_uid=payload.task_deps_uid,
            status=payload.status,
            notifications=payload.notifications,
            comment=payload.comment
        )
    except ValueError as e:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    if not new_task:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Task was not created")

    return new_task

@TaskRouter.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(task_id: int, taskService: TaskService = Depends()
):
    task = taskService.get_task_by_id(task_id)

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found")
    
    return taskService.delete(task)

@TaskRouter.get("/{task_id}")
def get_task_by_id(task_id: int, taskService: TaskService = Depends()
):
    task = taskService.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found")
    
    return task

@TaskRouter.get("/")
def get_tasks(task_id: int, taskService: TaskService = Depends()
):
    return taskService.get_tasks()

@TaskRouter.put("/{task_id}")
def update_task(task_id: int, data: dict, taskService: TaskService = Depends()
):
    task = get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    for key, value in data.items():
        if hasattr(task, key):
            setattr(task, key, value)
    
    return taskService.update(task)


# @app.post("/tasks/{task_id}", response_model=Task, status_code=201)
# def create_task222(task_id: int, payload: TaskCreate) -> Task:
#     if payload.id != task_id:
#         raise HTTPException(status_code=400, detail="Path task_id must match payload id")

#     try:
#         with get_connection() as connection:
#             row = connection.execute(
#                 text(
#                     """
#                     INSERT INTO tasks (id, name, task_group, employee, control, dependency, status, notifications, logs, comment)
#                     VALUES (:id, :name, :task_group, :employee, :control, :dependency, :status, :notifications, :logs, :comment)
#                     RETURNING *
#                     """
#                 ),
#                 {
#                     "id": payload.id,
#                     "name": payload.name,
#                     "task_group": payload.group,
#                     "employee": payload.employee,
#                     "control": payload.control,
#                     "dependency": payload.dependency,
#                     "status": payload.status,
#                     "notifications": payload.notifications,
#                     "logs": payload.logs,
#                     "comment": payload.comment,
#                 },
#             ).mappings().one()
#     except IntegrityError as exc:
#         raise HTTPException(status_code=409, detail="Task with this id already exists or dependency is invalid") from exc

#     return _task_from_row(row)


# @app.put("/tasks/{task_id}", response_model=Task)
# def replace_task(task_id: int, payload: TaskReplace) -> Task:
#     with get_connection() as connection:
#         row = connection.execute(
#             text(
#                 """
#                 UPDATE tasks
#                 SET name = :name,
#                     task_group = :task_group,
#                     employee = :employee,
#                     control = :control,
#                     dependency = :dependency,
#                     status = :status,
#                     notifications = :notifications,
#                     logs = :logs,
#                     comment = :comment
#                 WHERE id = :id
#                 RETURNING *
#                 """
#             ),
#             {
#                 "id": task_id,
#                 "name": payload.name,
#                 "task_group": payload.group,
#                 "employee": payload.employee,
#                 "control": payload.control,
#                 "dependency": payload.dependency,
#                 "status": payload.status,
#                 "notifications": payload.notifications,
#                 "logs": payload.logs,
#                 "comment": payload.comment,
#             },
#         ).mappings().first()

#     if row is None:
#         raise HTTPException(status_code=404, detail="Task not found")

#     return _task_from_row(row)

# def _task_from_row(row: dict) -> Task:
#     return Task(
#         id=int(row["id"]),
#         name=row["name"],
#         group=row["task_group"],
#         employee=row["employee"],
#         control=row["control"],
#         dependency=row["dependency"],
#         status=row["status"],
#         notifications=row["notifications"],
#         logs=row["logs"],
#         comment=row["comment"],
#     )