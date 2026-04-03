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
from ..models.TaskModel import TaskStatusEnum
from ..models.TaskRunningModel import RunningStatusEnum
from ..utils.datetime_utils import DateTimeUtils

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

MAX_WORKERS = 5
MAX_ATTEMPTS = 3
WAKE_UP_INTERVAL_SEC = 10
MIN_WAKE_UP_INTERVAL_SEC = 5
FROZEN_TASK_INTERVAL_SEC = 80
LISTEN_TIMEOUT_SEC = 5
WAIT_SEC = 0.3

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(threadName)s | %(message)s",
)
logger = logging.getLogger(__name__)


engine = create_engine(
    settings.database_url,
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


shutdown_event = threading.Event()
wake_up_workers = threading.Event()

is_skpped_old_ids = False
available_tasks = 0
current_workers = 0
active_workers_lock = threading.Lock()

def get_thread_num():
    num = 0
    try:
        result = threading.current_thread().name.split("_")[-1]

        if num is not None:
            num = int(result)
        return num + 1
    except Exception:
        return 0

def skip_old_ids_first_launch():
    current_dt = datetime.now()
    try:
        with SessionLocal.begin() as session:
            
            sql = text("""WITH cte AS (
                SELECT DISTINCT ON (tr.task_id)
                    tr.id
                FROM task_runnings tr
                WHERE 1 = 1
                AND tr.status = :pending
                AND tr.schedule_dt <= :now
                ORDER BY tr.task_id, tr.schedule_dt DESC     
                ),
                old_ids AS (
                SELECT id
                FROM task_runnings tr 
                WHERE tr.status = :pending
                AND tr.id NOT IN (SELECT id FROM cte)
                AND tr.schedule_dt <= :now
                )
                UPDATE task_runnings 
                SET status = :skipped
                WHERE id IN (SELECT * FROM old_ids)""")
            
            params =  {"now": current_dt, 
                        "skipped": RunningStatusEnum.SKIPPED.value, 
                        "pending": RunningStatusEnum.PENDING.value }
            
            session.execute(sql, params)

            logger.info("Old run ids skipped when app launched")

    except Exception as e:
        logger.error(f"Database error when skipping old ids: {e}", exc_info=True)

def claim_one_task(session):
    current_dt = datetime.now()
    worker_id = get_thread_num()

    task_ids_to_run, run_ids_to_run = get_available_tasks()

    if not task_ids_to_run or not run_ids_to_run:
        return None
    
    task_to_run = {"task_id": task_ids_to_run[0],
                   "run_id":  run_ids_to_run[0]}
        
    try:    
        session.execute(text("""
                                UPDATE tasks SET status = :running 
                                WHERE task_id = :task_id                
                                """), {
                                    "running": TaskStatusEnum.RUNNING.value,
                                    "task_id": task_to_run["task_id"]
                                    })
        session.commit()

        session.execute(text("""
                    UPDATE task_runnings 
                    SET started_dt = :now,
                    worker_id = :worker_id
                    WHERE id = :id                
                    """), {
                        "now": current_dt,
                        "worker_id": worker_id,
                        "id": task_to_run["run_id"]
                        })
        session.commit()

        # after no commit
        sql = text("""
                SELECT *
                FROM tasks 
                WHERE 1 = 1
                AND task_id = :task_id
                FOR UPDATE SKIP LOCKED
                LIMIT 1
        """)

        params = {
                "task_id": task_ids_to_run[0]
        }

        session.execute(sql, params)

        return task_to_run

    except Exception as e:
        logger.error(f"Database error while claiming task: {e}", exc_info=False)
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
        session = SessionLocal()
        task = claim_one_task(session)

        if task is None:
            update_available_tasks()
            logger.debug(f"Worker_id {get_thread_num()} - claimed task is none. AVAILABLE tasks amount {available_tasks}")
            return

        logger.debug(f'Worker_id {get_thread_num()}, get id task {task["run_id"]} with task id {task["task_id"]}')


        session.execute(text("""
                        UPDATE tasks SET status = :active 
                        WHERE task_id = :task_id                
                        """), {
                            "active": TaskStatusEnum.ACTIVE.value,
                            "task_id": task["task_id"]
                            })
        session.execute(text("""
                        UPDATE task_runnings 
                        SET finished_dt = :now,
                        status = :success
                        WHERE id = :id                
                        """), {
                            "now": datetime.now(),
                            "success": RunningStatusEnum.SUCCESS.value,
                            "id": task["run_id"]
                            })

        session.commit()
        # try:
        #     process_task(session, task)
        #     mark_task_done(session, task)

        # except Exception as exc:
        #     logger.exception(f'Worker_id {current_workers} - task id {task.task_id} failed')

        #     with SessionLocal.begin() as session:
        #         mark_task_retry(session, task.task_id, str(exc))

        with active_workers_lock:
            if available_tasks > 0:
                available_tasks -= 1
                logger.debug(f"Worker_id {current_workers} successed his job")
    except Exception as exc:
        logger.exception(f"Worker failed: {exc}")
        session.rollback()

    finally:
        with active_workers_lock:
            logger.debug(f"Worker_id {current_workers} - back to work")
            current_workers -= 1   
        session.close()
            

def get_available_tasks():
    global available_tasks
    try:
        with SessionLocal.begin() as session:
            current_dt = datetime.now()
            today = current_dt.date()

            task_ids = []
            run_ids = []
    
            result = session.execute(
                text("""
                    SELECT distinct task_id, run_id
                    FROM (
                        SELECT 
                            tr.task_id,
                            tr.id AS run_id,
                            ROW_NUMBER() OVER (PARTITION BY tr.task_id ORDER BY schedule_dt DESC) AS row_num
                        FROM task_runnings tr
                        JOIN tasks t ON tr.task_uid = t.task_uid
                        WHERE 1 = 1
                        AND tr.status = :pending                        
                        AND t.status != :running
                        AND tr.started_dt IS NULL
                        AND tr.created_dt::date = :today
                        AND tr.schedule_dt <= :now
                        AND (tr.attempt_count IS NULL OR tr.attempt_count <= :max_attempt)
                    ) sub
                    WHERE row_num = 1
                    ORDER BY task_id
                """),
                {"today": today, "now": current_dt, "max_attempt": MAX_ATTEMPTS, 
                 "running": TaskStatusEnum.RUNNING.value, "pending": RunningStatusEnum.PENDING.value }
            ).all()

        if not result:
            return task_ids, run_ids
        
        task_ids = [row.task_id for row in result]
        run_ids = [row.run_id for row in result]

        return task_ids, run_ids

    except Exception as e:
        logger.error(f"Database error while getting available tasks: {e}", exc_info=False)
        return task_ids, run_ids

def get_available_tasks_cout():
    task_ids, _ = get_available_tasks()
    return len(task_ids)

def update_available_tasks():
    global available_tasks
    with active_workers_lock:
        available_tasks = get_available_tasks_cout()
        logger.debug(f"AVAILABLE {available_tasks} tasks for run")

        

def dispatch_loop(executor: ThreadPoolExecutor):
    logger.info("Dispatcher started")

    while not shutdown_event.is_set():
        has_work = wake_up_workers.wait(timeout=WAIT_SEC)
        if not has_work:
            continue

        wake_up_workers.clear()

        if shutdown_event.is_set():
            break
        
        if available_tasks == 0:
            logger.debug("No available tasks for run")
            continue

        with active_workers_lock:
            free_workers = MAX_WORKERS - current_workers

        if free_workers <= 0:
            logger.debug("All workers are busy")
            continue

        for _ in range(free_workers):
            executor.submit(worker_job)

    logger.info("Dispatcher stopped")

def clear_status_for_frozen_task():
    pass

def interval_loop():

    logger.info(f"Interval loop started with every {WAKE_UP_INTERVAL_SEC} sec")

    skip_old_ids_first_launch()

    last_fallback = time.monotonic()
    min_last_fallback = time.monotonic()

    while not shutdown_event.is_set():            
        now = time.monotonic()
        
        if now - last_fallback >= WAKE_UP_INTERVAL_SEC:
            update_available_tasks()
            if available_tasks > 0:
                logger.debug(f"Wake-up after {WAKE_UP_INTERVAL_SEC} interval time")
                wake_up_workers.set()
            last_fallback = now
            min_last_fallback = now

        if available_tasks > 0 and (MAX_WORKERS - current_workers) > 0:
            if now - min_last_fallback >= MIN_WAKE_UP_INTERVAL_SEC:
                logger.debug("Wake-up again as available_tasks > 0")
                wake_up_workers.set()
                min_last_fallback = now
        
        if now - last_fallback >= FROZEN_TASK_INTERVAL_SEC:
            logger.info("Run script for clear status of frozen task")
            clear_status_for_frozen_task()
            last_fallback = now

        if shutdown_event.wait(timeout=WAIT_SEC):
            break


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