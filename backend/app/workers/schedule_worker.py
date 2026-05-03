import logging
import os
import select
import random
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from ..configs.Config import settings
from datetime import datetime, date
from ..models.TaskModel import Task, TaskStatusEnum
from ..models.TaskRunningModel import RunningStatusEnum
from ..services.TaskRunningService import TaskRunningService
from . import worker_services 
from sqlalchemy import create_engine, text, bindparam
from sqlalchemy.orm import sessionmaker
import asyncio

MAX_WORKERS = 5
MAX_ATTEMPTS = 3
WAKE_UP_INTERVAL_SEC = 10
MIN_WAKE_UP_INTERVAL_SEC = 5
LISTEN_TIMEOUT_SEC = 5
WAIT_SEC = 0.3


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

def dedublicate_runnings():
   with SessionLocal.begin() as session:
        try:
            sql = text("""DELETE FROM task_runnings
                WHERE id IN (
                    SELECT id
                    FROM (
                        SELECT
                            id,
                            ROW_NUMBER() OVER (
                                PARTITION BY
                                    task_uid,
                                    task_id,
                                    parent_uid,
                                    parent_id,
                                    trigger_mode,
                                    schedule_dt,
                                    notifications,
                                    email,
                                    tg_chat_id,
                                    storage_path,
                                    worker_id,
                                    started_dt,
                                    finished_dt,
                                    attempt_count,
                                    next_retry_at,
                                    status
                                ORDER BY id
                            ) AS rn
                        FROM task_runnings
                    ) t
                    WHERE t.rn > 1);""")
            
            session.execute(sql)

            logger.critical("Dedublicates successed in task_runnings")

        except Exception as e:
            logger.error(f"Database error when dedublicates running tasks: {e}", exc_info=True)

def get_thread_num():
    num = 0
    try:
        result = threading.current_thread().name.split("_")[-1]

        if num is not None:
            num = int(result)
        return num + 1
    except Exception:
        return 0
    
def refresh_task_runnings():
    with SessionLocal.begin() as session:
        try:
            task_running_service = TaskRunningService(session)
            task_running_service.refresh_runnings()
            logger.critical("Task_runnings refreshed in DB")
        except Exception as e:
            logger.error(f"Error while refreshing task_runnings in DB: {e}", exc_info=True)

def skip_old_ids_first_launch():
    current_dt = datetime.now()
    with SessionLocal.begin() as session:
        try:
            sql = text("""WITH cte AS (
                SELECT DISTINCT ON (tr.task_uid)
                    tr.id
                FROM task_runnings tr
                WHERE 1 = 1
                AND tr.status = :pending
                AND tr.schedule_dt <= :now
                ORDER BY tr.task_uid, tr.schedule_dt DESC     
                ),
                old_ids AS (
                SELECT id
                FROM task_runnings tr 
                WHERE (tr.status = :pending
                OR tr.status = :running)
                AND tr.id NOT IN (SELECT id FROM cte)
                AND tr.schedule_dt <= :now
                )
                UPDATE task_runnings 
                SET status = :skipped
                WHERE id IN (SELECT * FROM old_ids)""")
            
            params =  {"now": current_dt, 
                        "skipped": RunningStatusEnum.SKIPPED.value, 
                        "pending": RunningStatusEnum.PENDING.value,
                        "running": RunningStatusEnum.RUNNING.value
                        }
            
            session.execute(sql, params)

            logger.critical("Old run ids skipped when app launched")

        except Exception as e:
            logger.error(f"Database error when skipping old ids: {e}", exc_info=True)


def claim_one_task(session):
    current_dt = datetime.now()
    worker_id = get_thread_num()
    
    logger.critical(f'Claim_one_task worker id {get_thread_num()} started work')

    try:    
        row = session.execute(text("""
            WITH candidates AS (       
            SELECT
                tr.id AS run_id,
                tr.task_id,
                tr.task_uid
            FROM task_runnings tr
            JOIN tasks t ON tr.task_uid = t.task_uid
            WHERE tr.status = :pending
              AND t.on_control = 'on'
              AND t.run_expire_at < :now
              AND tr.created_dt::date = :today
              AND tr.schedule_dt <= :now
              AND (tr.attempt_count IS NULL OR tr.attempt_count < :max_attempt)
            ORDER BY tr.task_id
            LIMIT 10
            ),
            locked AS (
            SELECT task_id, run_id
            FROM candidates
            WHERE pg_try_advisory_xact_lock(task_uid) = true
            LIMIT 1
            )           
            UPDATE task_runnings tr
            SET status = :running
            FROM locked l
            WHERE tr.status = :pending
            AND tr.id = l.run_id
            RETURNING l.task_id, l.run_id, tr.attempt_count, tr.trigger_mode
        """), {
            "today": current_dt.date(),
            "now": current_dt,
            "max_attempt": MAX_ATTEMPTS,
            "pending": RunningStatusEnum.PENDING.value,
            "running": RunningStatusEnum.RUNNING.value
        }).fetchone()

        logger.critical(f'Row has {row} resultes worker id {worker_id}')
        if row is None:
            session.rollback()
            return None
        
        
        logger.critical(f'Claim_one_task worker id {worker_id} row {row.task_id}')

        task_to_run = {
            "task_id": row.task_id,
            "run_id": row.run_id,
            "attemps": row.attempt_count,
            "mode": row.trigger_mode}

        session.execute(text("""
            UPDATE task_runnings
            SET started_dt = :now,
                worker_id = :worker_id
            WHERE id = :id
        """), {
            "now": datetime.now(),
            "worker_id": worker_id,
            "id": task_to_run["run_id"]})

        with SessionLocal.begin() as task_session:
            task_session.execute(text("""
            UPDATE tasks t
            SET run_expire_at = :now + :sec * INTERVAL '1 second',
            last_run_at = :now
            WHERE task_id = :task_id
            """), {
            "now": datetime.now(),
            "sec": Task.TTL_RUN_SECONDS,
            "task_id": task_to_run["task_id"]
            })
            asyncio.run(worker_services.send_sse_request("task_update"))

        return task_to_run

    except Exception as e:
        logger.error(f"Database error while claiming task: {e}", exc_info=False)
        return None


def process_task(session, task):
    """
    Здесь твоя реальная логика.
    Пока просто пример.
    """
    task_id = task["task_id"]
    logger.critical("Processing task id=%s", task_id)


    time.sleep(2)

    logger.critical("Finished task id=%s", task_id)


def worker_job():
    time.sleep(random.uniform(0, 0.02))
    claimed_task = False
    is_successed = False
    global current_workers
    global available_tasks

    with active_workers_lock:
        current_workers += 1

    try:
        session = SessionLocal()
        task = claim_one_task(session)

        if task is not None:

            with active_workers_lock:
                if claimed_task and available_tasks > 0:
                    available_tasks -= 1
            logger.warning(f'Worker_id {get_thread_num()}, get run id {task["run_id"]} with task id {task["task_id"]}')

            session.commit()
            is_successed = worker_services.schedule_execute_task(task["task_id"], int(task.get("attemps") or 0) + 1, task["mode"])

            logger.warning(f'Worker_id {get_thread_num()}, finished task id {task["task_id"]} with is_successed result {is_successed}')

            if not is_successed:
                with SessionLocal.begin() as fail_session:
                    fail_session.execute(text("""
                        UPDATE task_runnings
                        SET attempt_count = COALESCE(attempt_count, 0) + 1,
                            schedule_dt = CASE WHEN COALESCE(attempt_count, 0) + 1 = :max_attempt THEN schedule_dt
                            ELSE :now + interval '30 seconds'
                            END,
                            next_retry_at = CASE WHEN COALESCE(attempt_count, 0) + 1 = :max_attempt THEN NULL
                            ELSE :now + interval '30 seconds'
                            END,
                            status = CASE WHEN COALESCE(attempt_count, 0) + 1 = :max_attempt THEN :error 
                            ELSE :pending
                            END
                        WHERE id = :run_id  
                    """), {
                        "max_attempt": MAX_ATTEMPTS,
                        "now": datetime.now(),
                        "run_id": task["run_id"],
                        "pending": RunningStatusEnum.PENDING.value,
                        "error": RunningStatusEnum.ERROR.value
                    })
                    fail_session.commit()
                    logger.warning(f'Worker_id {get_thread_num()}, set retry for {task["task_id"]} and run_id {task["run_id"]}')
            else:
                with SessionLocal.begin() as success_session: 
                    success_session.execute(text("""
                        UPDATE task_runnings 
                        SET finished_dt = :now,
                        status = :success
                        WHERE id = :id                
                        """), {
                            "now": datetime.now(),
                            "success": RunningStatusEnum.SUCCESS.value,
                            "id": task["run_id"]
                            })
                    success_session.commit()            
            
    except Exception as exc:
        logger.exception(f'Worker_id {get_thread_num()} failed task_id={task["task_id"]}: {exc}')
        session.rollback()

    finally:
        if task is not None:
            with SessionLocal.begin() as final_session:
                final_session.execute(text("""
                        UPDATE tasks 
                        SET run_expire_at = '1900-01-01' 
                        WHERE task_id = :task_id 
                    """), {
                        "task_id": task["task_id"]
                        })
                final_session.commit()
                asyncio.run(worker_services.send_sse_request("task_update"))

        with active_workers_lock:
            current_workers -= 1
            logger.warning(f"Worker_id {get_thread_num()} - back to work and available {MAX_WORKERS - current_workers} workers")
            

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
                        AND t.run_expire_at < :now
                        AND t.on_control = 'on'
                        AND tr.created_dt::date = :today
                        AND tr.schedule_dt <= :now
                        AND (tr.attempt_count IS NULL OR tr.attempt_count < :max_attempt)
                    ) sub
                    WHERE row_num = 1
                    ORDER BY task_id
                """),
                {"today": today, "now": current_dt, "max_attempt": MAX_ATTEMPTS, 
                 "pending": RunningStatusEnum.PENDING.value }
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
        logger.warning(f"AVAILABLE {available_tasks} tasks for run")

        

def dispatch_loop(executor: ThreadPoolExecutor):
    logger.critical("Dispatcher started")

    while not shutdown_event.is_set():
        has_work = wake_up_workers.wait(timeout=WAIT_SEC)
        if not has_work:
            continue

        wake_up_workers.clear()

        if shutdown_event.is_set():
            break
        
        with active_workers_lock:
            free_workers = MAX_WORKERS - current_workers

        if free_workers <= 0:
            logger.warning("All workers are busy")
            continue

        for _ in range(min(free_workers, available_tasks)):
            executor.submit(worker_job)

    logger.critical("Dispatcher stopped")


def interval_loop():
    
    launch_date = datetime.now().date()
    logger.critical(f"Interval loop started with every {WAKE_UP_INTERVAL_SEC} sec")

    refresh_task_runnings()
    dedublicate_runnings()
    skip_old_ids_first_launch()

    last_fallback = time.monotonic()
    min_last_fallback = time.monotonic()

    while not shutdown_event.is_set():            
        now = time.monotonic()
        
        if now - last_fallback >= WAKE_UP_INTERVAL_SEC:
            update_available_tasks()
            print(f"available {available_tasks} tasks and available {MAX_WORKERS - current_workers} workers")
            if available_tasks > 0:
                logger.critical(f"Wake-up after {WAKE_UP_INTERVAL_SEC} interval time")
                wake_up_workers.set()
            last_fallback = now
            min_last_fallback = now

        if available_tasks > 0 and (MAX_WORKERS - current_workers) > 0:
            if now - min_last_fallback >= MIN_WAKE_UP_INTERVAL_SEC:
                logger.critical(f"Wake-up again as available tasks still {available_tasks}")
                wake_up_workers.set()
                min_last_fallback = now

        now_date = datetime.now().date()
        if now_date > launch_date:
            logger.critical(f"New day has come: {now_date}")
            refresh_task_runnings()
            launch_date = now_date

        if shutdown_event.wait(timeout=WAIT_SEC):
            break


def handle_signal(signum, frame):
    logger.critical("Received signal %s, shutting down...", signum)
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

    logger.critical("Worker service started")
    logger.critical("Threads: main(listener) + dispatcher + up to %s workers", MAX_WORKERS)

    try:
        interval_loop()
    finally:
        shutdown_event.set()
        wake_up_workers.set()

        if executor:
            executor.shutdown(wait=False, cancel_futures=True)
    
        if dispatcher_thread and dispatcher_thread.is_alive():
            dispatcher_thread.join(timeout=5)

        import os
        import time
        def force_exit():
            time.sleep(10)
            logger.error("Force exit after timeout")
            os._exit(1)
        
        force_exit_thread = threading.Thread(target=force_exit, daemon=True)
        force_exit_thread.start()

        logger.critical("Worker service stopped")

if __name__ == "__main__":
    main()


