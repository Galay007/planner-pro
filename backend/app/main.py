import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from .routers.ConnectionRouter import ConnectionRouter
from .routers.TaskRouter import TaskRouter
from .routers.TaskHistRouter import TaskHistRouter
from .routers.TaskPropertyRouter import TaskPropertyRouter
from .models.TaskFileModel import TaskFile
from .models.TaskRunningModel import TaskRunning
from .models.TaskLogModel import TaskLog
from .configs.Config import settings
from .configs.Database import init_metadata_db
from .exceptions import register_db_exception_handlers
from contextlib import asynccontextmanager

# from sqlalchemy.ext.asyncio import AsyncSession, create_engine  # для ассинхронных запросов
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker

# @asynccontextmanager
# async def lifespan(_: FastAPI):
#     run_migrations()
#     yield

is_shutting_down = False

logging.basicConfig(
    level=logging.INFO,  # Минимальный уровень (INFO, DEBUG, WARNING, ERROR)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up application...")

    init_metadata_db()
    
    register_db_exception_handlers(app)
    
    print("✅ Application started")
    
    yield 

    global is_shutting_down
    is_shutting_down = True

    print("🛑 Shutting down application...")  


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(ConnectionRouter)
app.include_router(TaskRouter)
app.include_router(TaskHistRouter)
app.include_router(TaskPropertyRouter)

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

@app.get("/health")
def health() -> dict[str, str]:
    if is_shutting_down:
        return {"status": "shutting_down"}  # Для балансировщика нагрузки
    return {"status": "ok"}






