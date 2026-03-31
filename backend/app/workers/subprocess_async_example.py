import asyncio
import asyncpg
import subprocess
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskType(Enum):
    IO = "io"
    PYTHON_SCRIPT = "python_script"
    CPU = "cpu"


class TaskRunner:
    """Запуск задач разных типов"""
    
    def __init__(self, python_path: str = 'python', default_timeout: int = 300):
        self.python_path = python_path
        self.default_timeout = default_timeout
    
    async def run_io_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """I/O задача (API, файлы, сеть)"""
        try:
            action = payload.get('action')
            
            if action == 'http_request':
                # Пример HTTP запроса
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        payload['url'],
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        return {
                            'status': 'success',
                            'data': await response.text()
                        }
            
            elif action == 'file_operation':
                # Пример работы с файлами
                await asyncio.sleep(1)  # Имитация I/O
                return {'status': 'success', 'processed': True}
            
            else:
                # Общая I/O задача
                await asyncio.sleep(payload.get('duration', 1))
                return {'status': 'success'}
                
        except Exception as e:
            logger.error(f"IO task error: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def run_python_script(
        self,
        script_path: str,
        payload: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Запуск Python-скрипта через subprocess"""
        timeout = timeout or self.default_timeout
        script_path = Path(script_path).absolute()
        
        if not script_path.exists():
            return {
                'status': 'error',
                'error': f'Script not found: {script_path}'
            }
        
        start_time = datetime.now()
        logger.info(f"Running script: {script_path}")
        
        try:
            # Асинхронный запуск subprocess
            process = await asyncio.create_subprocess_exec(
                self.python_path,
                str(script_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(script_path.parent)
            )
            
            # Отправляем payload и ждём завершения с таймаутом
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(
                        input=json.dumps(payload).encode()
                    ),
                    timeout=timeout
                )
                
                elapsed = (datetime.now() - start_time).total_seconds()
                
                if process.returncode == 0:
                    logger.info(f"Script completed in {elapsed}s")
                    return {
                        'status': 'success',
                        'output': json.loads(stdout.decode()) if stdout else {},
                        'stdout': stdout.decode(),
                        'stderr': stderr.decode(),
                        'elapsed': elapsed
                    }
                else:
                    logger.error(f"Script failed: {stderr.decode()}")
                    return {
                        'status': 'failed',
                        'error': stderr.decode(),
                        'stdout': stdout.decode(),
                        'returncode': process.returncode,
                        'elapsed': elapsed
                    }
                    
            except asyncio.TimeoutError:
                logger.error(f"Script timeout after {timeout}s")
                process.kill()
                await process.wait()
                return {
                    'status': 'timeout',
                    'error': f'Timeout after {timeout}s',
                    'elapsed': timeout
                }
                
        except Exception as e:
            logger.error(f"Script execution error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def run_task(
        self,
        task_type: TaskType,
        payload: Dict[str, Any],
        script_path: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Универсальный метод запуска задач"""
        
        if task_type == TaskType.PYTHON_SCRIPT:
            if not script_path:
                return {'status': 'error', 'error': 'script_path required'}
            return await self.run_python_script(script_path, payload, timeout)
        
        elif task_type == TaskType.IO:
            return await self.run_io_task(payload)
        
        else:
            return {'status': 'error', 'error': f'Unknown task type: {task_type}'}


class TaskScheduler:
    """Основной планировщик задач"""
    
    def __init__(
        self,
        dsn: str,
        max_concurrent_tasks: int = 50,
        python_path: str = 'python',
        default_timeout: int = 300
    ):
        self.dsn = dsn
        self.max_concurrent_tasks = max_concurrent_tasks
        self.python_path = python_path
        self.default_timeout = default_timeout
        
        self.pool: Optional[asyncpg.Pool] = None
        self.runner = TaskRunner(python_path, default_timeout)
        self.semaphore: Optional[asyncio.Semaphore] = None
        self.running = False
    
    async def connect(self):
        """Подключение к БД"""
        self.pool = await asyncpg.create_pool(
            self.dsn,
            min_size=5,
            max_size=self.max_concurrent_tasks,
            command_timeout=60
        )
        self.semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        logger.info(f"Connected to database (max tasks: {self.max_concurrent_tasks})")
    
    async def disconnect(self):
        """Отключение от БД"""
        if self.pool:
            await self.pool.close()
        logger.info("Disconnected from database")
    
    async def fetch_task(self) -> Optional[tuple]:
        """Получение одной задачи из БД"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow("""
                    SELECT id, name, task_type, payload, script_path, timeout
                    FROM tasks
                    WHERE status = 'pending'
                      AND scheduled_at <= NOW()
                    ORDER BY priority DESC, scheduled_at
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                """)
                
                if not row:
                    return None
                
                # Помечаем как running
                await conn.execute("""
                    UPDATE tasks
                    SET status = 'running',
                        started_at = NOW(),
                        worker_id = %s
                    WHERE id = %s
                """, f"worker-{asyncio.current_task().get_name()}", row['id'])
                
                return tuple(row)
    
    async def update_task_status(
        self,
        task_id: int,
        status: str,
        result: Dict[str, Any]
    ):
        """Обновление статуса задачи"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE tasks
                SET status = %s,
                    completed_at = NOW(),
                    error_message = %s,
                    result = %s
                WHERE id = %s
            """, status, result.get('error'), json.dumps(result), task_id)
            
            # Логирование
            await conn.execute("""
                INSERT INTO task_logs (task_id, message, level)
                VALUES (%s, %s, %s)
            """, task_id, f"Task completed: {status}", 
                  'ERROR' if status == 'failed' else 'INFO')
    
    async def process_task(self, task: tuple):
        """Обработка одной задачи"""
        task_id, name, task_type, payload, script_path, timeout = task
        
        try:
            logger.info(f"Processing task {task_id}: {name} (type: {task_type})")
            
            # Запускаем задачу
            result = await self.runner.run_task(
                task_type=TaskType(task_type),
                payload=payload or {},
                script_path=script_path,
                timeout=timeout or self.default_timeout
            )
            
            # Обновляем статус
            await self.update_task_status(task_id, result['status'], result)
            logger.info(f"Task {task_id} completed: {result['status']}")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed with exception: {e}")
            await self.update_task_status(task_id, 'failed', {'error': str(e)})
    
    async def worker(self, worker_id: int):
        """Воркер - бесконечный цикл обработки задач"""
        logger.info(f"Worker {worker_id} started")
        
        while self.running:
            async with self.semaphore:
                task = await self.fetch_task()
            
            if not task:
                await asyncio.sleep(5)  # Нет задач - ждём
                continue
            
            await self.process_task(task)
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def start(self, num_workers: int = 10):
        """Запуск планировщика"""
        await self.connect()
        self.running = True
        
        logger.info(f"Starting scheduler with {num_workers} workers")
        
        # Создаём воркеров
        workers = [
            asyncio.create_task(self.worker(i), name=f"worker-{i}")
            for i in range(num_workers)
        ]
        
        # Ждём завершения (никогда, если не остановить)
        await asyncio.gather(*workers, return_exceptions=True)
    
    async def stop(self):
        """Остановка планировщика"""
        self.running = False
        logger.info("Stopping scheduler...")
        await self.disconnect()


# ==================== ПРИМЕР ИСПОЛЬЗОВАНИЯ ====================

async def main():
    scheduler = TaskScheduler(
        dsn="postgresql://user:password@localhost:5432/mydb",
        max_concurrent_tasks=50,
        python_path='/path/to/venv/bin/python',
        default_timeout=300
    )
    
    try:
        await scheduler.start(num_workers=10)
    except KeyboardInterrupt:
        await scheduler.stop()


if __name__ == '__main__':
    asyncio.run(main())