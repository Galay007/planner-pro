import { useState, useEffect, useCallback, useRef } from 'react';
import { connectSSE, disconnectSSE } from '../../services/sse';
import { getTaskRunnings, parseApiError } from '../../services/api';
import type { TaskRunningOut, ServerMessage } from '../../types';
import RunningToolbar from './RunningToolbar';
import RunningTable from './RunningTable';
import './MonitoringPage.css';

type StatusFilter = 'success' | 'error' | 'skipped' | 'pending';

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function monthStartStr() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
}

export default function MonitoringPage() {
  const [rows, setRows] = useState<TaskRunningOut[]>([]);
  const [search, setSearch] = useState('');
  const [sseStatus, setSseStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [serverMessage, setServerMessage] = useState<ServerMessage | null>(null);
  const [dateFrom, setDateFrom] = useState(monthStartStr());
  const [dateTo, setDateTo] = useState(todayStr());
  const [statusFilter, setStatusFilter] = useState<Set<StatusFilter>>(new Set());
  const msgTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const pushMessage = useCallback((msg: ServerMessage) => {
    setServerMessage(msg);
    if (msgTimer.current) clearTimeout(msgTimer.current);
    msgTimer.current = setTimeout(() => setServerMessage(null), 8000);
  }, []);

  function fetchRunnings(isRefresh = false) {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);
    getTaskRunnings()
      .then(({ data, status }) => {
        setRows(Array.isArray(data) ? data : []);
        pushMessage({ status, text: 'Все OK', ok: true });
      })
      .catch((e) => {
        const { status, detail } = parseApiError(e);
        setError(detail ?? 'Ошибка загрузки');
        pushMessage({ status, text: 'Ошибка загрузки', detail, ok: false });
      })
      .finally(() => {
        setLoading(false);
        setRefreshing(false);
      });
  }

  useEffect(() => {
    document.body.classList.toggle('is-loading', loading || refreshing);
  }, [loading, refreshing]);

  useEffect(() => { fetchRunnings(); }, []);

  useEffect(() => {
    connectSSE({
      onOpen: () => setSseStatus('connected'),
      onError: () => setSseStatus('error'),
      onRunningRefresh: () => fetchRunnings(true),
    });
    return () => disconnectSSE();
  }, []);

  function toggleStatus(s: StatusFilter) {
    setStatusFilter(prev => {
      const next = new Set(prev);
      if (next.has(s)) next.delete(s);
      else next.add(s);
      return next;
    });
  }

  const filtered = rows.filter(r => {
    if (statusFilter.size > 0 && !statusFilter.has((r.status ?? '') as StatusFilter)) return false;
    if (dateFrom && r.schedule_dt.slice(0, 10) < dateFrom) return false;
    if (dateTo && r.schedule_dt.slice(0, 10) > dateTo) return false;
    if (search) {
      const q = search.toLowerCase();
      return (
        String(r.task_id).includes(q) ||
        (r.task_name ?? '').toLowerCase().includes(q) ||
        (r.trigger_mode ?? '').toLowerCase().includes(q) ||
        (r.status ?? '').toLowerCase().includes(q) ||
        r.schedule_dt.includes(q) ||
        (r.started_str ?? '').includes(q)
      );
    }
    return true;
  });

  return (
    <div className="monitoring">
      <div className="monitoring__header">
        <h1 className="monitoring__title">Мониторинг</h1>
        <div className={`scheduler__sse-indicator scheduler__sse-indicator--${sseStatus}`}>
          SSE: {sseStatus === 'connected' ? 'подключён' : sseStatus === 'error' ? 'ошибка' : 'подключение...'}
        </div>
      </div>

      <RunningToolbar
        onRefresh={() => fetchRunnings(true)}
        refreshing={refreshing}
        dateFrom={dateFrom}
        dateTo={dateTo}
        onDateFromChange={setDateFrom}
        onDateToChange={setDateTo}
        statusFilter={statusFilter}
        onStatusToggle={toggleStatus}
        onStatusClear={() => setStatusFilter(new Set())}
      />

      <div className="scheduler__search-bar">
        <div className="search-input-wrap">
          <span className="search-icon">🔍</span>
          <input
            className="search-input"
            type="text"
            placeholder="Поиск..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        {search && (
          <button className="btn-reset" onClick={() => setSearch('')}>✕ Сбросить</button>
        )}
        {serverMessage && (
          <div className={`server-msg${serverMessage.ok ? '' : ' server-msg--err'}`}>
            {!serverMessage.ok && serverMessage.detail && (
              <span>{serverMessage.status} - {serverMessage.detail}</span>
            )}
          </div>
        )}
      </div>

      {loading && <div className="scheduler__state">Загрузка...</div>}
      {error && <div className="scheduler__state scheduler__state--error">{error}</div>}
      {!loading && <RunningTable rows={filtered} />}
    </div>
  );
}
