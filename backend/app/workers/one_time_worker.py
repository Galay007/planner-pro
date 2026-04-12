import logging
from sqlalchemy import create_engine, text, bindparam
from sqlalchemy.orm import sessionmaker
import sys
import time
import os
import threading

logger = logging.getLogger(__name__)

PID = None
STORAGE_PATH = None
TASK_ID = None
DB_URL = None
TTL_RUN_SECONDS = None
INTERVAL_SEC = 25
WAIT_SEC = 1

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

def main_job():
    try:
        logger.info(f"Work has been started")
        print('Начал работу')
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

        except Exception as e:
            logger.error(f"Error finish run while one-time run: {e}", exc_info=True)

def interval_loop():
    last_fallback = time.monotonic()

    while not stop_event.is_set():            
        now = time.monotonic()

        if now - last_fallback >= INTERVAL_SEC:
            print('interval')
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


def main():
    get_storag_path()

    heartbeat_thread = threading.Thread(target=interval_loop, daemon=True)
    heartbeat_thread.start()

    main_job()

    finish_run()


if __name__ == "__main__":
    PID = os.getpid()
    TASK_ID = sys.argv[1]
    TTL_RUN_SECONDS = int(sys.argv[2])
    DB_URL = sys.argv[3]

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
    
    #input("Нажмите Enter, чтобы завершить...") # если хотим, чтобы окно не закрывалось
