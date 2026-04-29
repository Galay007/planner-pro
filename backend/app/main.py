import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from .routers.ConnectionRouter import ConnectionRouter
from .routers.TaskRouter import TaskRouter
from .routers.TaskRunningRouter import TaskRunningRouter
from .routers.TaskPropertyRouter import TaskPropertyRouter
from .routers.TaskLogRouter import TaskLogRouter
from .models.TaskFileModel import TaskFile
from .models.TaskRunningModel import TaskRunning
from .models.TaskLogModel import TaskLog
from .configs.Config import settings
from .utils.SSEManager import SSEManager
from .configs.Database import init_metadata_db
from .exceptions import register_db_exception_handlers
from .services.SseService import set_sse_manager
from .schemas.SseSchema import EmitRequest
from contextlib import asynccontextmanager
import asyncio
import os


is_shutting_down = False
sse_manager: SSEManager | None = None

DIST_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "dist")

logging.basicConfig(
    level=logging.INFO,  # Минимальный уровень (INFO, DEBUG, WARNING, ERROR)
    format="%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global sse_manager, is_shutting_down

    init_metadata_db()

    sse_manager = SSEManager()
    set_sse_manager(sse_manager)
    
    register_db_exception_handlers(app)
    
    print("Application started")
    
    yield 

    is_shutting_down = True
    await sse_manager.shutdown() 

    print("Shutting down application...")  



app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(ConnectionRouter, prefix="/api")
app.include_router(TaskRouter, prefix="/api")
app.include_router(TaskRunningRouter, prefix="/api")
app.include_router(TaskPropertyRouter, prefix="/api")
app.include_router(TaskLogRouter, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

@app.get("/health")
def health() -> dict[str, str]:
    if is_shutting_down:
        return {"status": "shutting_down"} 
    return {"status": "ok"}

@app.get("/sse")
async def sse_endpoint(request: Request):
    if sse_manager is None:
        raise RuntimeError("SSE manager is not initialized")
    
    return StreamingResponse(
        sse_manager.add_client(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

@app.post("/sse/emit")
async def emit_event(request: EmitRequest ):
    await sse_manager.broadcast(request.message, request.event_type)
    return {"ok": True}


if os.path.isdir(DIST_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        file_path = os.path.join(DIST_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", 
        host = settings.host,
        port =settings.port,
        reload=True,   
        log_level="info"
    )







