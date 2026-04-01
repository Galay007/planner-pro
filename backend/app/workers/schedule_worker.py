import logging
import os
import select
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ==========================================
# CONFIG
# ==========================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres",
)


MAX_WORKERS = 5
WAKE_UP_INTERVAL_SEC = 30
FROZEN_TASK_INTERVAL_SEC = 120
LISTEN_TIMEOUT_SEC = 5
DISPATCHER_WAIT_SEC = 1

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(threadName)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ==========================================
# SQLAlchemy
# ==========================================

engine = create_engine(
    DATABASE_URL,
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
                next_retry_at = now() + interval '30 seconds',
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

    # здесь может быть твой I/O:
    # - запросы в БД
    # - вызов внешнего API
    # - отправка письма
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
                logger.info(f"Worker_id {current_workers} - no tasks available")
                return

            try:
                process_task(session, task)
                mark_task_done(session, task)

            except Exception as exc:
                logger.exception(f"Worker_id {current_workers} - task id {task["task_id"]} failed")

                with SessionLocal.begin() as session:
                    mark_task_retry(session, task["id"], str(exc))

        with active_workers_lock:
            if available_tasks > 0:
                available_tasks -= 1
    finally:
        with active_workers_lock:
            current_workers -= 1
            

def update_available_tasks():
    pass

def dispatch_loop(executor: ThreadPoolExecutor):
    logger.info("Dispatcher started")

    while not shutdown_event.is_set():
        has_work = wake_up_workers.wait(timeout=DISPATCHER_WAIT_SEC)
        if not has_work:
            continue

        wake_up_workers.clear()

        if shutdown_event.is_set():
            break
        
        update_available_tasks()

        with active_workers_lock:
            free_workers = MAX_WORKERS - current_workers

        if free_workers <= 0:
            logger.info("No free worker")
            break

        logger.info("Submitting %s worker(s)", free_workers)

        for _ in range(free_workers):
            executor.submit(worker_job)

        time.sleep(0.3)


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

    with ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="schedule-worker") as executor:
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
            dispatcher_thread.join(timeout=5)

        logger.info("Worker service stopped")


if __name__ == "__main__":
    main()