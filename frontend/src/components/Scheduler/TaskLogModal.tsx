import { useEffect, useState } from 'react';
import type { TaskLogOut } from '../../types';
import './TaskLogModal.css';

interface Props {
  taskId: number;
  logs: TaskLogOut[];
  onClose: () => void;
}

function formatDt(dt: string | null): string {
  if (!dt) return '';
  // return dt.replace('T', ' ').replace(/(\.\d{2})\d*$/, '$1');
  return dt.replace('T', ' ').replace(/\.\d*$/, '');
}

export default function TaskLogModal({ taskId, logs, onClose }: Props) {
  const [search, setSearch] = useState('');

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, []);

  const q = search.toLowerCase();
  const filtered = q
    ? logs.filter(log =>
        (log.created_dt ?? '').toLowerCase().includes(q) ||
        (log.file_name ?? '').toLowerCase().includes(q) ||
        String(log.pid_id ?? '').includes(q) ||
        (log.log_text ?? '').toLowerCase().includes(q)
      )
    : logs;

  return (
    <div className="log-overlay">
      <div className="log-modal" onClick={e => e.stopPropagation()}>
        <div className="log-modal__header">
          <span className="log-modal__title">Логи задачи #{taskId}</span>
          <button className="log-modal__close" onClick={onClose}>✕</button>
        </div>
        <div className="log-modal__search">
          <input
            className="log-modal__search-input"
            type="text"
            placeholder="Поиск..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <div className="log-modal__body">
          <table className="log-table">
            <thead>
              <tr>
                <th className="log-table__th">Дата</th>
                <th className="log-table__th">Скрипт</th>
                <th className="log-table__th">PID</th>
                <th className="log-table__th log-table__th--text">Лог</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={4} className="log-table__empty">Нет данных</td>
                </tr>
              ) : (
                filtered.map((log, i) => (
                  <tr key={i} className="log-table__row">
                    <td className="log-table__td log-table__td--dt">{formatDt(log.created_dt)}</td>
                    <td className="log-table__td log-table__td--file">{log.file_name ?? ''}</td>
                    <td className="log-table__td log-table__td--pid">{log.pid_id ?? ''}</td>
                    <td className="log-table__td log-table__td--text">{log.log_text ?? ''}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
