# worker_task.py
from sqlalchemy import create_engine
from .services.ConnectionService import get_connection_by_name

def run_job_using_connection(conn_name: str):
    conn = get_connection_by_name(conn_name)
    if not conn:
        raise RuntimeError(f"Connection '{conn_name}' not found")

    db_url = conn.build_sqlalchemy_url()

    engine = create_engine(db_url, future=True)
    with engine.connect() as db_conn:
        # пример: простая проверка
        result = db_conn.execute("SELECT 1")
        print("DB result:", list(result))
