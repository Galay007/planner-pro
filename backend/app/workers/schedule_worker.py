import logging
import os
import select
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from ..configs.Config import settings
from datetime import datetime, date

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

MAX_WORKERS = 5
MAX_ATTEMPTS = 3
WAKE_UP_INTERVAL_SEC = 10
FROZEN_TASK_INTERVAL_SEC = 80
LISTEN_TIMEOUT_SEC = 5
DISPATCHER_WAIT_SEC = 1

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(threadName)s | %(message)s",
)
logger = logging.getLogger(__name__)


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    future=True,
)


shutdown_event = threading.Event()
wake_up_workers = threading.Event()

available_tasks = 0
current_workers = 0
active_workers_lock = threading.Lock()



def claim_one_task(session):

    sql = text("""
        WITH cte AS (
            SELECT id
            FROM tasks
            WHERE status IN ('new', 'retry')
              AND (next_retry_at IS NULL OR next_retry_at <= now())
            ORDER BY id
            FOR UPDATE SKIP LOCKED
            LIMIT 1
        )
        UPDATE tasks t
        SET status = 'processing',
            started_at = now()
        FROM cte
        WHERE t.id = cte.id
        RETURNING t.id, t.payload;
    """)

    try:
        row = session.execute(sql).mappings().first()
        return row
    except Exception as e:
        logger.error(f"Database error while claiming task: {e}", exc_info=True)
        return None


def mark_task_done(session, task_id: int):
    session.execute(
        text("""
            UPDATE tasks
            SET status = 'done',
                finished_at = now(),
                last_error = NULL
            WHERE id = :task_id
        """),
        {"task_id": task_id},
    )


def mark_task_retry(session, task_id: int, error_text: str):
    session.execute(
        text("""
            UPDATE tasks
            SET status = 'retry',
                attempt_count = COALESCE(attempt_count, 0) + 1,
                schedule_dt = now() + interval '30 seconds',
                last_error = :error_text
            WHERE id = :task_id
        """),
        {"task_id": task_id, "error_text": error_text[:1000]},
    )


def process_task(session, task):
    """
    Здесь твоя реальная логика.
    Пока просто пример.
    """
    task_id = task["task_id"]
    logger.info("Processing task id=%s", task_id)


    time.sleep(2)

    logger.info("Finished task id=%s", task_id)


def worker_job():
    global current_workers
    global available_tasks

    with active_workers_lock:
        current_workers += 1

    try:
        with SessionLocal.begin() as session:
            task = claim_one_task(session)

            if not task:
                available_tasks = 0
                logger.debug(f"Worker_id {current_workers} - no tasks available")
                return

            try:
                process_task(session, task)
                mark_task_done(session, task)

            except Exception as exc:
                logger.exception(f'Worker_id {current_workers} - task id {task["task_id"]} failed')

                with SessionLocal.begin() as session:
                    mark_task_retry(session, task["id"], str(exc))

        with active_workers_lock:
            if available_tasks > 0:
                available_tasks -= 1
    finally:
        with active_workers_lock:
            current_workers -= 1
            

def get_available_tasks():
    global available_tasks
    try:
        with SessionLocal.begin() as session:
            today = date.today()
            now = datetime.now()
    
            available_tasks = session.execute(
                text("""
                    SELECT COUNT(task_id)
                    FROM (
                        SELECT 
                            tr.task_id,
                            ROW_NUMBER() OVER (PARTITION BY tr.task_id ORDER BY schedule_dt DESC) AS row_num
                            FROM task_runnings tr
                            JOIN tasks t ON tr.task_uid = t.task_uid
                            WHERE tr.status = 'pending'
                            AND t.status != 'running'
                            AND tr.started_dt IS NULL
                            AND tr.created_dt::date = :today
                            AND tr.schedule_dt <= :now
                            AND (tr.attempt_count IS NULL OR tr.attempt_count <= :max_attempt)
                    ) sub
                    WHERE row_num = 1
                """),
                {"today": today, "now": now, "max_attempt": MAX_ATTEMPTS}
            ).scalar()

            if available_tasks == 0:
                logger.debug(f"Available {available_tasks} tasks for run")

    except Exception as e:
        logger.error(f"Database error while getting available tasks: {e}", exc_info=True)

        

def dispatch_loop(executor: ThreadPoolExecutor):
    logger.info("Dispatcher started")

    while not shutdown_event.is_set():
        has_work = wake_up_workers.wait(timeout=DISPATCHER_WAIT_SEC)
        if not has_work:
            continue

        wake_up_workers.clear()

        if shutdown_event.is_set():
            break
        
        get_available_tasks()

        if available_tasks == 0:
            logger.debug("No available tasks for run")
            break

        with active_workers_lock:
            free_workers = MAX_WORKERS - current_workers

        if free_workers <= 0:
            logger.debug("No free worker")
            break

        logger.debug("Submitting %s worker(s)", free_workers)

        for _ in range(free_workers):
            executor.submit(worker_job)

    logger.info("Dispatcher stopped")

def clear_status_for_frozen_task():
    pass

def interval_loop():

    logger.info(f"Interval loop started with every {WAKE_UP_INTERVAL_SEC} sec")

    last_fallback = time.monotonic()

    while not shutdown_event.is_set():

        now = time.monotonic()
        if now - last_fallback >= WAKE_UP_INTERVAL_SEC:
            logger.info("Wake-up from interval time")
            wake_up_workers.set()
            last_fallback = now

        if available_tasks > 0:
            wake_up_workers.set()
        
        if now - last_fallback >= FROZEN_TASK_INTERVAL_SEC:
            logger.info("Run script for clear status of frozen task")
            clear_status_for_frozen_task()  


def handle_signal(signum, frame):
    logger.info("Received signal %s, shutting down...", signum)
    shutdown_event.set()
    wake_up_workers.set()


def main():
    signal.signal(signal.SIGINT, handle_signal) # сигнал прерывания (нажатие Ctrl+C в терминале)
    signal.signal(signal.SIGTERM, handle_signal) # сигнал завершения (например, от kill <pid> или оркестратора docker/k8

    executor = ThreadPoolExecutor(
        max_workers=MAX_WORKERS,
        thread_name_prefix="schedule-worker"
    )
    
    dispatcher_thread = threading.Thread(
        target=dispatch_loop,
        args=(executor,),
        name="dispatcher-thread",
        daemon=True,
    )
    dispatcher_thread.start()

    logger.info("Worker service started")
    logger.info("Threads: main(listener) + dispatcher + up to %s workers", MAX_WORKERS)

    try:
        interval_loop()
    finally:
        shutdown_event.set()
        wake_up_workers.set()

        if executor:
            executor.shutdown(wait=False, cancel_futures=True)
    
        if dispatcher_thread and dispatcher_thread.is_alive():
            dispatcher_thread.join(timeout=5)

        # import os
        # import time
        # def force_exit():
        #     time.sleep(10)
        #     logger.error("Force exit after timeout")
        #     os._exit(1)
        
        # force_exit_thread = threading.Thread(target=force_exit, daemon=True)
        # force_exit_thread.start()

        # logger.info("Worker service stopped")

if __name__ == "__main__":
    main()


    # Ручное управление 
    # def process_with_manual_commit():
    # session = SessionLocal()
    # try:
    #     result = do_something(session)
        
    #     session.commit()
    #     return result
        
    # except Exception:
    #     session.rollback()
    #     raise
    # finally:
    #     session.close()