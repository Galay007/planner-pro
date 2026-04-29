import logging
from sqlalchemy import create_engine, text, bindparam
from sqlalchemy.orm import sessionmaker, Session
from ..configs.Config import settings
import sys
import time
import os
import threading
import requests
from ..models import TaskModel
from ..models import TaskPropertyModel
from ..models import TaskFileModel
from ..models import ConnectionModel
from ..services.TaskLogService import TaskLogService
from ..services.TaskFileService import TaskFileService
import sys, traceback

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

PID = None
TASK_ID = None
TASK_TYPE = None
TASK_DB_URL = None
TTL_RUN_SECONDS = None
INTERVAL_SEC = 25
WAIT_SEC = 1
TASK_UPDATE_EVENT = "task_update"

stop_event = threading.Event()
taskLogService: TaskLogService
taskFileService: TaskFileService

def get_files():
    return taskFileService.get_by_id(TASK_ID)

def sql_job_execute(script_file: TaskFileModel):

    with open(script_file.file_path, 'r') as full_script:
        content = full_script.read()

        script_list = [part.strip() for part in content.split(";") if part.strip()]

        count = 1
        for sql in script_list:
            send_log(TASK_ID,f"Разовый запуск: внутренний скрипт № {count} страт", script_file.file_name)
            
            execute_sql(sql)

            send_log(TASK_ID,f"Разовый запуск: внутренний скрипт № {count} финиш", script_file.file_name)

            count += 1

def execute_sql(sql: str): 
    with taskDBSession.begin() as session:
        session.execute(text(sql))
        session.commit()  
        
        logger.info(f"Task id {TASK_ID} has been executed")
        time.sleep(5)


def finish_run():
    with taskDBSession.begin() as session:
        try:
            session.execute(text("""
            UPDATE tasks
            SET run_expire_at = '1900-01-01'
            WHERE task_id = :task_id
            """),
            {"task_id": TASK_ID})
            session.commit()

        except Exception as e:
            logger.error(f"Error finish run while one-time run: {e}", exc_info=True)

def interval_loop():
    last_fallback = time.monotonic()

    while not stop_event.is_set():            
        now = time.monotonic()

        if now - last_fallback >= INTERVAL_SEC:
            logger.info(f"Sending heartbeat after {INTERVAL_SEC} seconds")
            send_heartbeat()
            last_fallback = now

        if stop_event.wait(timeout=WAIT_SEC):
            break


def send_heartbeat():
    with taskDBSession.begin() as session:
        try:
            session.execute(text("""
            UPDATE tasks
            SET run_expire_at = NOW() + (:ttl_seconds || ' seconds')::interval
            WHERE task_id = :task_id
            """),
            {"ttl_seconds": TTL_RUN_SECONDS, "task_id": TASK_ID})

            
        except Exception as e:
            logger.error(f"Error finish run while one-time run: {e}", exc_info=True)

def send_log(task_id, log_text, file_name: str = None):
        taskLogService.create(task_id, log_text, file_name)
        taskLogService.commit()

def send_sse_request(event_type: str):
    try:
        SSE_URL = f"http://localhost:{settings.port}/sse/emit"
        requests.post(SSE_URL,json={"message": "{}", "event_type": event_type},timeout=(5.0, 0.001))
        logger.info(f"Sent sse request")

    except Exception as e:
        logger.error(f"Error while sending sse_request: {e}")
        pass 


def main():
    heartbeat_thread = threading.Thread(target=interval_loop, daemon=True)
    heartbeat_thread.start()
    
    send_log(TASK_ID,f"Разовый запуск: задача {TASK_ID} с типом '{TASK_TYPE}' начал работу")

    script_files = get_files()
    for script_file in script_files:
        if TASK_TYPE == 'sql':
            sql_job_execute(script_file)
             
    send_log(TASK_ID,f"Разовый запуск: задача {TASK_ID} с типом '{TASK_TYPE} успешно отработал'")

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


if __name__ == "__main__":
    try:
        PID = os.getpid()
        TASK_ID = int(sys.argv[1])
        TASK_TYPE = sys.argv[2]
        TTL_RUN_SECONDS = int(sys.argv[3])
        TASK_DB_URL = sys.argv[4]

        logger.info(f"PID {PID} has started")
        
        metaDbSession = get_db_connection(settings.database_url)
        
        taskDBSession = get_db_connection(TASK_DB_URL)

        taskLogService = TaskLogService(metaDbSession())
        taskFileService = TaskFileService(metaDbSession())

        main()
        logger.info(f"PID {PID} has finished")
    except Exception as exc:
        str = traceback.format_exc(limit=-3)
        send_log(TASK_ID,f"Ошибка: {str}")
        traceback.print_exception(exc, limit=2, file=sys.stdout)
    finally: 
        finish_run()
        send_sse_request(TASK_UPDATE_EVENT)
        stop_event.set()
        #input("Нажмите Enter, чтобы завершить...") # если хотим, чтобы окно не закрывалось
        pass
