import subprocess
import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskRunner:
    def __init__(self, python_path='python', default_timeout=300):
        self.python_path = python_path
        self.default_timeout = default_timeout
    
    def run_task(self, script_path, payload, timeout=None, env=None):
        """Запуск задачи с полным логированием"""
        timeout = timeout or self.default_timeout
        script_path = Path(script_path).absolute()
        
        if not script_path.exists():
            return {
                'status': 'error',
                'error': f'Script not found: {script_path}'
            }
        
        start_time = datetime.now()
        logger.info(f"Starting task: {script_path}")
        
        try:
            result = subprocess.run(
                [self.python_path, str(script_path)],
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env or {},
                cwd=script_path.parent
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if result.returncode == 0:
                logger.info(f"Task completed in {elapsed}s")
                return {
                    'status': 'success',
                    'output': json.loads(result.stdout) if result.stdout else {},
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'elapsed': elapsed
                }
            else:
                logger.error(f"Task failed: {result.stderr}")
                return {
                    'status': 'failed',
                    'error': result.stderr,
                    'stdout': result.stdout,
                    'returncode': result.returncode,
                    'elapsed': elapsed
                }
                
        except subprocess.TimeoutExpired as e:
            logger.error(f"Task timeout after {timeout}s")
            return {
                'status': 'timeout',
                'error': f'Timeout after {timeout}s',
                'stdout': e.stdout.decode() if e.stdout else '',
                'stderr': e.stderr.decode() if e.stderr else ''
            }
        except Exception as e:
            logger.error(f"Task error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

# Использование в планировщике
runner = TaskRunner(python_path='/path/to/venv/bin/python', default_timeout=600)

def worker(worker_id, dsn):
    import psycopg
    conn = psycopg.connect(dsn)
    
    with conn.cursor() as cur:
        while True:
            cur.execute("""
                SELECT id, payload, script_path, timeout
                FROM tasks
                WHERE status = 'pending'
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            """)
            
            task = cur.fetchone()
            if not task:
                break
            
            task_id, payload, script_path, timeout = task
            
            # Запускаем скрипт
            result = runner.run_task(script_path, payload, timeout)
            
            # Сохраняем результат
            cur.execute("""
                UPDATE tasks 
                SET status = %s, 
                    completed_at = NOW(), 
                    error_message = %s,
                    result = %s
                WHERE id = %s
            """, [result['status'], result.get('error'), 
                  json.dumps(result), task_id])
            conn.commit()
    
    conn.close()