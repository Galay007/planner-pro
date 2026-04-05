import { useState, useEffect } from 'react';
import { connectSSE, disconnectSSE } from '../../services/sse';
import { getTasks, deleteTask } from '../../services/api';
import type { TaskOut, TaskRunning } from '../../types';
import TaskToolbar from './TaskToolbar';
import TaskTable from './TaskTable';
import './SchedulerPage.css';

export default function SchedulerPage() {
  const [tasks, setTasks] = useState<TaskOut[]>([]);
  const [taskRunnings, setTaskRunnings] = useState<TaskRunning[]>([]);
  const [search, setSearch] = useState('');
  const [sseStatus, setSseStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);

  function fetchTasks(isRefresh = false) {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);
    getTasks()
      .then(setTasks)
      .catch((e) => setError(e?.message ?? 'Ошибка загрузки задач'))
      .finally(() => {
        setLoading(false);
        setRefreshing(false);
      });
  }

  useEffect(() => {
    fetchTasks();
  }, []);

  useEffect(() => {
    connectSSE({
      onOpen: () => setSseStatus('connected'),
      onError: () => setSseStatus('error'),
      onTasks: (data) => setTasks(data),
      onTaskRunnings: (data) => setTaskRunnings(data),
    });
    return () => disconnectSSE();
  }, []);

  async function handleDelete() {
    if (selectedId === null) return;
    setDeleting(true);
    try {
      await deleteTask(selectedId);
      setTasks((prev) => prev.filter((t) => t.task_id !== selectedId));
      setSelectedId(null);
    } catch (e) {
      console.error('Delete failed', e);
    } finally {
      setDeleting(false);
    }
  }

  const filteredTasks = tasks.filter((t) => {
    const q = search.toLowerCase();
    return (
      String(t.task_id).includes(q) ||
      t.task_name.toLowerCase().includes(q) ||
      (t.task_group ?? '').toLowerCase().includes(q) ||
      t.owner.toLowerCase().includes(q)
    );
  });

  return (
    <div className="scheduler">
      <div className="scheduler__header">
        <h1 className="scheduler__title">Планировщик задач</h1>
        <div className={`scheduler__sse-indicator scheduler__sse-indicator--${sseStatus}`}>
          SSE: {sseStatus === 'connected' ? 'подключён' : sseStatus === 'error' ? 'ошибка' : 'подключение...'}
        </div>
      </div>

      <TaskToolbar
        onRefresh={() => fetchTasks(true)}
        refreshing={refreshing}
        selectedId={selectedId}
        onDelete={handleDelete}
        deleting={deleting}
      />

      <div className="scheduler__search-bar">
        <div className="search-input-wrap">
          <span className="search-icon">🔍</span>
          <input
            className="search-input"
            type="text"
            placeholder="Поиск..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        {search && (
          <button className="btn-reset" onClick={() => setSearch('')}>
            ✕ Сбросить
          </button>
        )}
      </div>

      {loading && <div className="scheduler__state">Загрузка...</div>}
      {error && <div className="scheduler__state scheduler__state--error">{error}</div>}

      {!loading && (
        <TaskTable
          tasks={filteredTasks}
          taskRunnings={taskRunnings}
          onTasksChange={setTasks}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
      )}
    </div>
  );
}
