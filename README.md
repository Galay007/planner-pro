# Schedule Buddy Backend (Python + REST + PostgreSQL 15)

FastAPI backend for scheduler tasks from `src/pages/Scheduler.tsx` / `src/types/task.ts`.

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy (Core)
- PostgreSQL 15

## Run PostgreSQL 15

```bash
cd backend
docker compose up -d
```

## Run API

```shell
cd backend
python -m venv .venv
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Auto migration on startup

When the API starts, it automatically runs SQL migrations (`CREATE TABLE IF NOT EXISTS`) for:

- `tasks`
- `task_properties`

## REST endpoints

- `GET /health`
- `GET /tasks`
- `GET /tasks/{task_id}`
- `POST /tasks/{task_id}`
- `PATCH /tasks/{task_id}`
- `DELETE /tasks/{task_id}`
- `GET /tasks/{task_id}/properties`
- `POST /tasks/{task_id}/properties`
- `DELETE /tasks/{task_id}/properties/{property_key}`

## Schema mapping to frontend

`tasks` fields map to frontend `Task` shape:

- `id`
- `name`
- `task_group` ↔ `group`
- `employee`
- `control` (`play` / `stop`)
- `dependency`
- `status` (`idle` / `running` / `success` / `error`)
- `notifications`
- `logs`
- `comment`

`task_properties` stores per-task properties as key/value pairs:

- `id`
- `task_id`
- `property_key`
- `property_value`
