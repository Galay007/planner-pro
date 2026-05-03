import logging
from sqlalchemy import create_engine, text, bindparam
from sqlalchemy.orm import sessionmaker, Session
from ..configs.Config import settings
import sys
import time
import os
import threading
import requests
from ..models.TaskModel import Task
from ..models.ConnectionModel import Connection
from ..models.TaskFileModel import TaskFile
from ..models.TaskRunningModel import TaskRunning, TriggerModeEnum, RunningStatusEnum
from ..repositories.TaskRepository import TaskRepository
from ..services.TaskRunningService import TaskRunningService
from ..services.TaskLogService import TaskLogService
from ..services.TaskFileService import TaskFileService
import sys, traceback
from ..configs.Database import get_orm_connection
import httpx
from datetime import datetime
from typing import List
from ..utils.DatetimeUtils import DateTimeUtils

taskRepository: TaskRepository
task_mode = ''
WAIT_SEC = 1

logger = logging.getLogger(__name__)

async def send_sse_request(event_type: str):
    try:
        SSE_URL = f"http://localhost:{settings.port}/sse/emit"
        async with httpx.AsyncClient() as client:
            await client.post(SSE_URL,json={"message": "{}", "event_type": event_type},timeout=httpx.Timeout(5.0, read=0.001))

    except Exception as e:
        logger.error(f"Error while sending sse_request: {e}")
        pass 


def interval_loop(ttl_run_seconds: int, task_id: int, stop_event: threading.Event):
    last_fallback = time.monotonic()
    
    while not stop_event.is_set():            
        now = time.monotonic()

        if now - last_fallback >= ttl_run_seconds - 5:
            send_heartbeat(ttl_run_seconds, task_id)
            last_fallback = now

        if stop_event.wait(timeout=WAIT_SEC):
            break


def send_heartbeat(ttl_run_seconds: int, task_id: int):
    with get_db_connection(settings.database_url).begin() as session: 
        try:
            session.execute(text("""
            UPDATE tasks
            SET run_expire_at = :now + :ttl_seconds * INTERVAL '1 second'
            WHERE task_id = :task_id
            """),
            {"now": datetime.now(), "ttl_seconds": ttl_run_seconds, "task_id": task_id})

            
        except Exception as e:
            logger.error(f"Error finish run while schedule run: {e}", exc_info=True)

def sql_job_execute(script_file: TaskFile, task_db: Session, task_id: int):

    with open(script_file.file_path, 'r') as full_script:
        content = full_script.read()

        script_list = [part.strip() for part in content.split(";") if part.strip()]

        count = 1
        for sql in script_list:
            send_log(task_id,f"запуск: внутренний скрипт № {count} старт", script_file.file_name)
            
            execute_sql(sql, task_db, task_id)

            send_log(task_id,f"запуск: внутренний скрипт № {count} финиш", script_file.file_name)

            count += 1

def execute_sql(sql: str, task_session: Session, task_id: int): 
        task_session.execute(text(sql))
        task_session.commit()  
        
        logger.warning(f"Task id {task_id} has been executed")

def send_log(task_id, log_text, file_name: str = None):
    full_log_text = f"{get_prefix()} {log_text}"
    try:
        with get_db_connection(settings.database_url).begin() as session: 
            taskLogService = TaskLogService(session)
            taskLogService.create(task_id, full_log_text, file_name)
            taskLogService.commit()
    except Exception as exc:
        logger.error(f"Exception problem with DB {exc}")

def get_task(task_id: int) -> Task:
    return taskRepository.get_task_by_task_id_long(task_id)

def get_children_by_task_id(task_id) -> List[Task]:
    return taskRepository.get_childs_by_parent_id(task_id)

def send_runnings_for_children(parent_task_id: int):

    childrens = get_children_by_task_id(parent_task_id)

    if len(childrens) == 0:
        return 
    
    for task in childrens:
        logger.warning(f"Found children {task.task_id} with parent {task.task_deps_id}")
        
        if task.run_expire_at > DateTimeUtils.local_wo_microsec():
            continue

        base_fields  = dict(
                    task_uid = task.task_uid,
                    task_id = task.task_id,
                    parent_id = task.task_deps_id,
                    trigger_mode = TriggerModeEnum.DEPENDED.value,
                    notifications = task.notifications,
                    email = task.task_props.email,
                    tg_chat_id = task.task_props.tg_chat_id,
                    storage_path = task.task_props.storage_path,
                    schedule_dt = DateTimeUtils.local_wo_microsec(),
                    created_dt = DateTimeUtils.local_wo_microsec(),
                    status = RunningStatusEnum.PENDING.value
                )

        new_run = TaskRunning(**base_fields)
        try:
            with get_db_connection(settings.database_url).begin() as session: 
                taskRunningService = TaskRunningService(session)
                taskRunningService.create_task_run(new_run)
                session.commit()
        except Exception as exc:
            logger.error(f"Exception problem with DB {exc}")

def get_db_connection(url: str) -> Session:
    engine = create_engine(
            url,
            pool_pre_ping=True,
            future=True,
            echo=False
        )
    SessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    ) 
    return SessionLocal

def get_prefix():
    if task_mode == TriggerModeEnum.DEPENDED:
        return 'Зависимый'
    if task_mode == TriggerModeEnum.SCHEDULED:
        return 'Плановый'

def schedule_execute_task(task_id: int, attemps: int, mode: str) -> bool:
    heartbeat_thread = None
    stop_event = threading.Event()

    global taskRepository
    global task_mode
    task_mode = mode
    is_successed = False
    meta_session = None
    task_session = None
    try:
        metaDB = get_db_connection(settings.database_url)
        meta_session = metaDB()
        taskRepository = TaskRepository(meta_session)
        
        task = get_task(task_id)
        task_type = task.task_props.task_type

        heartbeat_thread = threading.Thread(
            target=interval_loop,
            args=(task.TTL_RUN_SECONDS, task_id, stop_event),
            daemon=True
        )
        heartbeat_thread.start()

        send_log(task_id,f"запуск: задача {task_id} с типом '{task_type}' начал работу, попытка {attemps}")

        taskDB = get_db_connection(task.db_url)
        task_session = taskDB()
        if task.task_props.files is not None:         
            for script_file in task.task_props.files:
                if task.task_props.task_type == 'sql':
                    sql_job_execute(script_file, task_session, task_id)

            is_successed = True
        
        send_log(task_id,f"запуск: задача {task_id} с типом '{task_type}' успешно отработал, попытка {attemps}")
        
        logger.warning(f"Started search children of {task_id}...")
        send_runnings_for_children(task_id)
      
    except Exception as exc:
        exc_str = traceback.format_exc(limit=-3)
        send_log(task_id,f"Ошибка: {exc_str}")
        traceback.print_exception(exc, limit=2, file=sys.stdout)
    finally:
        if heartbeat_thread and heartbeat_thread.is_alive():
            stop_event.set()
            heartbeat_thread.join(timeout=1)      
        for session in [meta_session, task_session]:
            if session is not None:
                try:
                    session.close()
                except Exception:
                    pass
    return is_successed 








