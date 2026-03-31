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

CHANNEL_NAME = "new_task"
MAX_WORKERS = 5
FALLBACK_WAKEUP_SEC = 30
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

# ==========================================
# SHARED STATE
# ==========================================

shutdown_event = threading.Event()
wake_up_workers = threading.Event()

active_workers = 0
active_workers_lock = threading.Lock()


# ==========================================
# TASK SQL
# Подстрой под свою таблицу tasks / task_properties
# ==========================================

def claim_one_task(session):
    """
    Атомарно забирает одну задачу.
    Здесь использована абстрактная таблица tasks.
    Подстрой SQL под свою реальную модель.
    """
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

    row = session.execute(sql).mappings().first()
    return row


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


# ==========================================
# BUSINESS LOGIC
# ==========================================

def process_task(task_row: dict):
    """
    Здесь твоя реальная логика.
    Пока просто пример.
    """
    task_id = task_row["id"]
    logger.info("Processing task id=%s", task_id)

    # здесь может быть твой I/O:
    # - запросы в БД
    # - вызов внешнего API
    # - отправка письма
    time.sleep(2)

    logger.info("Finished task id=%s", task_id)


# ==========================================
# WORKER
# ==========================================

def worker_job():
    global active_workers

    with active_workers_lock:
        active_workers += 1

    try:
        # 1. claim task
        with SessionLocal.begin() as session:
            task = claim_one_task(session)

        if not task:
            logger.info("No tasks available")
            return

        try:
            # 2. process
            process_task(task)

            # 3. mark done
            with SessionLocal.begin() as session:
                mark_task_done(session, task["id"])

        except Exception as exc:
            logger.exception("Task failed id=%s", task["id"])

            with SessionLocal.begin() as session:
                mark_task_retry(session, task["id"], str(exc))

    finally:
        with active_workers_lock:
            active_workers -= 1


# ==========================================
# DISPATCHER
# ==========================================

def dispatch_loop(executor: ThreadPoolExecutor):
    logger.info("Dispatcher started")

    while not shutdown_event.is_set():
        fired = wake_up_workers.wait(timeout=DISPATCHER_WAIT_SEC)
        if not fired:
            continue

        wake_up_workers.clear()

        while not shutdown_event.is_set():
            with active_workers_lock:
                free_slots = MAX_WORKERS - active_workers

            if free_slots <= 0:
                logger.info("No free worker slots")
                break

            logger.info("Submitting %s worker(s)", free_slots)

            for _ in range(free_slots):
                executor.submit(worker_job)

            # Даём воркерам время забрать задачи
            time.sleep(0.3)

            # Один проход за wakeup обычно достаточно.
            # Если задач много, следующий wakeup придёт либо от poll, либо от notify.
            break

    logger.info("Dispatcher stopped")


# ==========================================
# LISTENER IN MAIN THREAD
# ==========================================

def listen_loop():
    """
    Listener работает в main thread.

    Важно:
    - создаём raw_connection через SQLAlchemy engine
    - LISTEN регистрируем SQL-командой
    - ждём уведомления через select.select(...)
    - fallback: раз в 30 секунд поднимаем wake_up_workers
    """

    logger.info("Listener started in main thread, channel=%s", CHANNEL_NAME)

    raw_conn = engine.raw_connection()

    try:
        # для LISTEN/NOTIFY нужен autocommit
        raw_conn.autocommit = True

        cursor = raw_conn.cursor()
        cursor.execute(f"LISTEN {CHANNEL_NAME};")

        last_fallback = time.monotonic()

        while not shutdown_event.is_set():
            ready = select.select([raw_conn], [], [], LISTEN_TIMEOUT_SEC)

            if ready == ([], [], []):
                now = time.monotonic()
                if now - last_fallback >= FALLBACK_WAKEUP_SEC:
                    logger.info("Fallback wakeup")
                    wake_up_workers.set()
                    last_fallback = now
                continue

            # читаем уведомления у DBAPI connection
            raw_conn.poll()

            notifies = getattr(raw_conn, "notifies", [])
            while notifies:
                notify = notifies.pop(0)
                logger.info("Got NOTIFY: %s", getattr(notify, "payload", None))
                wake_up_workers.set()

            now = time.monotonic()
            if now - last_fallback >= FALLBACK_WAKEUP_SEC:
                logger.info("Fallback wakeup after notify")
                wake_up_workers.set()
                last_fallback = now

    finally:
        with suppress(Exception):
            cursor.close()
        with suppress(Exception):
            raw_conn.close()

        logger.info("Listener stopped")


# ==========================================
# SIGNALS
# ==========================================

def handle_signal(signum, frame):
    logger.info("Received signal %s, shutting down...", signum)
    shutdown_event.set()
    wake_up_workers.set()


# ==========================================
# MAIN
# ==========================================

def main():
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="task-worker") as executor:
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
            # main thread = listener
            listen_loop()
        finally:
            shutdown_event.set()
            wake_up_workers.set()
            dispatcher_thread.join(timeout=5)

        logger.info("Worker service stopped")


if __name__ == "__main__":
    main()