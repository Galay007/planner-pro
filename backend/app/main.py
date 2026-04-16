import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
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
from .utils.SSEManager import SSEManager
from .configs.Database import init_metadata_db
from .exceptions import register_db_exception_handlers
from .services.SseService import set_sse_manager
from .schemas.SseSchemas import EmitRequest
from contextlib import asynccontextmanager
import asyncio


is_shutting_down = False
sse_manager: SSEManager | None = None

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

app.include_router(ConnectionRouter)
app.include_router(TaskRouter)
app.include_router(TaskHistRouter)
app.include_router(TaskPropertyRouter)

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



if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", 
        host = settings.host,
        port =settings.port,
        reload=True,   
        log_level="info"
    )







