import { useState, useEffect, useCallback, useRef } from 'react';
import { useBlocker } from 'react-router-dom';
import { connectSSE, disconnectSSE } from '../../services/sse';
import { getTasks, deleteTask, getMaxTaskId, createTask, parseApiError } from '../../services/api';
import type { TaskOut, ServerMessage } from '../../types';
import TaskToolbar from './TaskToolbar';
import TaskTable from './TaskTable';
import './SchedulerPage.css';
import {Logger} from '../../utils/logger'

export default function SchedulerPage() {
  const [tasks, setTasks] = useState<TaskOut[]>([]);
  const [search, setSearch] = useState('');
  const [sseStatus, setSseStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [adding, setAdding] = useState(false);
  const [serverMessage, setServerMessage] = useState<ServerMessage | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const msgTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const blocker = useBlocker(({ currentLocation, nextLocation }) =>
    editingId !== null && currentLocation.pathname !== nextLocation.pathname
  );

  useEffect(() => {
    const busy = loading || refreshing || adding || deleting;
    document.body.classList.toggle('is-loading', busy);
  }, [loading, refreshing, adding, deleting]);

  const pushMessage = useCallback((msg: ServerMessage) => {
    setServerMessage(msg);
    if (msgTimer.current) clearTimeout(msgTimer.current);
    msgTimer.current = setTimeout(() => setServerMessage(null), 5000);
  }, []);

  function fetchTasks(isRefresh = false) {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);
    getTasks()
      .then(({ data, status }) => {
        setTasks(data);
        Logger.info('Received get task request', data)
        pushMessage({ status, text: 'Все OK', ok: true });
      })
      .catch((e) => {
        const { status, detail } = parseApiError(e);
        setError(detail ?? 'Ошибка загрузки задач');
        pushMessage({ status, text: 'Ошибка загрузки', detail, ok: false });
      })
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
      onRefresh: () => fetchTasks(true)
    });
    return () => disconnectSSE();
  }, []);

  async function handleAdd() {
    setAdding(true);
    try {
      const maxId = await getMaxTaskId();
      const { status } = await createTask(maxId + 1);
      pushMessage({ status, text: 'Задача создана', ok: true });
      //fetchTasks(true); теперь через sse
    } catch (e) {
      const { status, detail } = parseApiError(e);
      pushMessage({ status, text: 'Ошибка создания задачи', detail, ok: false });
      console.error('Add failed', e);
    } finally {
      setAdding(false);
    }
  }

  async function handleDelete() {
    if (selectedId === null) return;
    setDeleting(true);
    try {
      const { status } = await deleteTask(selectedId);
      pushMessage({ status, text: `Задача #${selectedId} удалена`, ok: true });
      setSelectedId(null);
      //fetchTasks(true); теперь через sse
    } catch (e) {
      const { status, detail } = parseApiError(e);
      pushMessage({ status, text: 'Ошибка удаления', detail, ok: false });
      console.error('Delete failed', e);
    } finally {
      setDeleting(false);
    }
  }

  const filteredTasks = tasks.filter((t) => {
    const q = search.toLowerCase();
    return (
      String(t.task_id).includes(q) ||
      t.on_control.toLowerCase().includes(q) ||
      t.task_name.toLowerCase().includes(q) ||
      (t.task_group ?? '').toLowerCase().includes(q) ||
      (t.schedule ?? '').toLowerCase().includes(q) ||
      (t.next_run_at ?? '').toLowerCase().includes(q) ||
      (t.last_run_at ?? '').toLowerCase().includes(q) ||
      t.owner.toLowerCase().includes(q) ||
      t.status.toLowerCase().includes(q)
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
        selectedId={selectedId}
        refreshing={refreshing}
        onRefresh={() => fetchTasks(true)}
        adding={adding}
        editing={editingId !== null}
        onAdd={handleAdd}
        deleting={deleting}
        onDelete={handleDelete}
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

        {serverMessage && (
          <div className={`server-msg${serverMessage.ok ? '' : ' server-msg--err'}`}>
            {/* <span className="server-msg__status">{serverMessage.status}</span>
            <span className="server-msg__text">{serverMessage.text}</span> */}
            {!serverMessage.ok && serverMessage.detail && (
              <span>{serverMessage.status} - {serverMessage.detail}</span>
            )}
          </div>
        )}
      </div>

      {loading && <div className="scheduler__state">Загрузка...</div>}
      {error && <div className="scheduler__state scheduler__state--error">{error}</div>}

      {!loading && (
        <TaskTable
          tasks={filteredTasks}
          selectedId={selectedId}
          editingId={editingId}
          setEditingId={setEditingId}
          onSelect={setSelectedId}
          onRefresh={() => fetchTasks(true)}
          onServerMessage={pushMessage}
        />
      )}

      {blocker.state === 'blocked' && (
        <div className="nav-block-overlay">
          <div className="nav-block-dialog">
            <p className="nav-block-dialog__text">Есть несохранённые изменения. Покинуть страницу?</p>
            <div className="nav-block-dialog__btns">
              <button className="nav-block-dialog__btn nav-block-dialog__btn--cancel" onClick={() => blocker.reset?.()}>
                Остаться
              </button>
              <button className="nav-block-dialog__btn nav-block-dialog__btn--confirm" onClick={() => blocker.proceed?.()}>
                Покинуть
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}