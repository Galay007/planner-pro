import { useState } from 'react';
import type { TaskOut, TaskRunning } from '../../types';
import { startTask, stopTask } from '../../services/api';
import './TaskTable.css';

interface Props {
  tasks: TaskOut[];
  taskRunnings: TaskRunning[];
  onTasksChange: (tasks: TaskOut[]) => void;
  selectedId: number | null;
  onSelect: (id: number | null) => void;
}

type SortKey = keyof TaskOut;
type SortDir = 'asc' | 'desc';

export default function TaskTable({ tasks, taskRunnings, onTasksChange, selectedId, onSelect }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('task_id');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const [loadingIds, setLoadingIds] = useState<Set<number>>(new Set());

  const runningIds = new Set(taskRunnings.map((r) => r.task_id));

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  }

  const sorted = [...tasks].sort((a, b) => {
    const av = a[sortKey] ?? '';
    const bv = b[sortKey] ?? '';
    if (av < bv) return sortDir === 'asc' ? -1 : 1;
    if (av > bv) return sortDir === 'asc' ? 1 : -1;
    return 0;
  });

  async function handleControl(task: TaskOut) {
    const id = task.task_id;
    setLoadingIds((prev) => new Set(prev).add(id));
    try {
      if (task.on_control === 'off') {
        await startTask(id);
        onTasksChange(tasks.map((t) => (t.task_id === id ? { ...t, on_control: 'on' } : t)));
      } else {
        await stopTask(id);
        onTasksChange(tasks.map((t) => (t.task_id === id ? { ...t, on_control: 'off' } : t)));
      }
    } catch (e) {
      console.error('Control action failed', e);
    } finally {
      setLoadingIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  }

  function SortIcon({ col }: { col: SortKey }) {
    if (sortKey !== col) return <span className="sort-icon sort-icon--inactive">↕</span>;
    return <span className="sort-icon">{sortDir === 'asc' ? '↑' : '↓'}</span>;
  }

  function ColHeader({ label, col }: { label: string; col: SortKey }) {
    return (
      <th className="table__th" onClick={() => handleSort(col)}>
        {label} <SortIcon col={col} />
      </th>
    );
  }

  return (
    <div className="table-wrap">
      <table className="task-table">
        <thead>
          <tr>
            <ColHeader label="ID" col="task_id" />
            <th className="table__th">Управление</th>
            <ColHeader label="Имя задачи" col="task_name" />
            <ColHeader label="Группа" col="task_group" />
            <ColHeader label="Автор" col="owner" />
            <ColHeader label="Статус" col="status" />
            <ColHeader label="След. запуск" col="schedule" />
            <ColHeader label="Связь с ID" col="task_deps_id" />
            <th className="table__th">Уведомл.</th>
            <th className="table__th">Логи</th>
            <th className="table__th">Комментарий</th>
          </tr>
        </thead>
        <tbody>
          {sorted.length === 0 ? (
            <tr>
              <td colSpan={11} className="table__empty">Нет данных</td>
            </tr>
          ) : (
            sorted.map((task) => (
              <TaskRow
                key={task.task_id}
                task={task}
                isRunning={runningIds.has(task.task_id)}
                isLoading={loadingIds.has(task.task_id)}
                isSelected={selectedId === task.task_id}
                onControl={handleControl}
                onSelect={onSelect}
              />
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

interface RowProps {
  task: TaskOut;
  isRunning: boolean;
  isLoading: boolean;
  isSelected: boolean;
  onControl: (task: TaskOut) => void;
  onSelect: (id: number | null) => void;
}

function TaskRow({ task, isRunning, isLoading, isSelected, onControl, onSelect }: RowProps) {
  const statusClass =
    task.status === 'running' ? 'status--running'
    : task.status === 'error' ? 'status--error'
    : 'status--stopped';

  const statusLabel =
    task.status === 'running' ? 'Выполняется'
    : task.status === 'error' ? 'Ошибка'
    : task.status === 'stopped' ? 'Остановлен'
    : task.status;

  const isOn = task.on_control === 'on';

  function handleRowClick(e: React.MouseEvent) {
    // Don't deselect when clicking interactive elements
    if ((e.target as HTMLElement).closest('button, input, a')) return;
    onSelect(isSelected ? null : task.task_id);
  }

  return (
    <tr
      className={[
        'table__row',
        isRunning ? 'table__row--running' : '',
        isSelected ? 'table__row--selected' : '',
      ].filter(Boolean).join(' ')}
      onClick={handleRowClick}
    >
      <td className="table__td table__td--id">{task.task_id}</td>

      {/* Управление — тумблер */}
      <td className="table__td table__td--controls">
        <button
          className={`toggle${isOn ? ' toggle--on' : ''}${isLoading ? ' toggle--loading' : ''}`}
          title={isOn ? 'Остановить' : 'Запустить'}
          disabled={isLoading}
          onClick={() => onControl(task)}
        >
          <span className="toggle__thumb" />
        </button>
      </td>

      <td className="table__td">{task.task_name}</td>
      <td className="table__td">{task.task_group ?? <span className="muted">—</span>}</td>
      <td className="table__td">{task.owner}</td>

      <td className="table__td">
        <span className={`status-badge ${statusClass}`}>{statusLabel}</span>
      </td>

      <td className="table__td">{task.schedule ?? <span className="muted">—</span>}</td>
      <td className="table__td">{task.task_deps_id ?? <span className="muted">—</span>}</td>

      <td className="table__td table__td--center">
        <input type="checkbox" checked={task.notifications} readOnly />
      </td>

      <td className="table__td">
        <button className="link-btn">Открыть</button>
      </td>

      <td className="table__td">{task.comment ?? <span className="muted">—</span>}</td>
    </tr>
  );
}
