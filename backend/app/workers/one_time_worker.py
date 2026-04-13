import logging
from sqlalchemy import create_engine, text, bindparam
from sqlalchemy.orm import sessionmaker
from ..configs.Config import settings
import sys
import time
import os
import threading
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

PID = None
STORAGE_PATH = None
TASK_ID = None
TASK_TYPE = None
DB_URL = None
TTL_RUN_SECONDS = None
INTERVAL_SEC = 25
WAIT_SEC = 1
TASK_UPDATE_EVENT = "task_update"

stop_event = threading.Event()

def get_storag_path():
   global STORAGE_PATH
   with SessionLocal.begin() as session:
        try:
            result = session.execute(text("""
            SELECT storage_path
            FROM task_runnings
            WHERE task_id = :task_id
            """),
            {"task_id": TASK_ID}).scalar()

            if result:
                STORAGE_PATH = result

        except Exception as e:
            logger.error(f"Error get storage while one-time run: {e}", exc_info=True)

def sql_job_execute():
    try:
        logger.info(f"Task id {TASK_ID} has been executed")
        time.sleep(10)
        
    finally:
        stop_event.set()

def finish_run():
    with SessionLocal.begin() as session:
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
            sendHeartBeat()
            last_fallback = now

        if stop_event.wait(timeout=WAIT_SEC):
            break


def sendHeartBeat():
    with SessionLocal.begin() as session:
        try:
            session.execute(text("""
            UPDATE tasks
            SET run_expire_at = NOW() + (:ttl_seconds || ' seconds')::interval
            WHERE task_id = :task_id
            """),
            {"ttl_seconds": TTL_RUN_SECONDS, "task_id": TASK_ID})

            
        except Exception as e:
            logger.error(f"Error finish run while one-time run: {e}", exc_info=True)


def send_sse_request(event_type: str):
    try:
        SSE_URL = f"http://localhost:{settings.port}/sse/emit"
        requests.post(SSE_URL,json={"message": "{}", "event_type": event_type},timeout=(5.0, 0.001))
        logger.info(f"Sent sse request")

    except Exception as e:
        logger.error(f"Error while sending sse_request: {e}")
        pass 

def main():
    get_storag_path()

    heartbeat_thread = threading.Thread(target=interval_loop, daemon=True)
    heartbeat_thread.start()

    if TASK_TYPE == 'sql':
        sql_job_execute()
        send_sse_request(TASK_UPDATE_EVENT)
        
    finish_run()


if __name__ == "__main__":
    PID = os.getpid()
    TASK_ID = sys.argv[1]
    TASK_TYPE = sys.argv[2]
    TTL_RUN_SECONDS = int(sys.argv[3])
    DB_URL = sys.argv[4]

    logger.info(f"PID {PID} has started")
    engine = create_engine(
        DB_URL,
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

    main()
    
    # input("Нажмите Enter, чтобы завершить...") # если хотим, чтобы окно не закрывалось
