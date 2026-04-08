import { useState } from 'react';
import type { TaskOut, TaskRunning, ServerMessage } from '../../types';
import { startTask, stopTask, parseApiError } from '../../services/api';
import './TaskTable.css';

interface Props {
  tasks: TaskOut[];
  taskRunnings: TaskRunning[];
  selectedId: number | null;
  onSelect: (id: number | null) => void;
  onRefresh: () => void;
  onServerMessage: (msg: ServerMessage) => void;
}

type SortKey = keyof TaskOut;
type SortDir = 'asc' | 'desc';

export default function TaskTable({ tasks, taskRunnings, selectedId, onSelect, onServerMessage }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('task_id');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
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
    try {
      if (task.on_control === 'off') {
        const { status } = await startTask(id);
        onServerMessage({ status, text: `Задача #${id} запущена`, ok: true });
      } else {
        const { status } = await stopTask(id);
        onServerMessage({ status, text: `Задача #${id} остановлена`, ok: true });
      }
    } catch (e) {
      const { status, detail } = parseApiError(e);
      onServerMessage({ status, text: 'Ошибка управления', detail, ok: false });
      console.error('Control action failed', e);
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
  isSelected: boolean;
  onControl: (task: TaskOut) => void;
  onSelect: (id: number | null) => void;
}

function TaskRow({ task, isRunning, isSelected, onControl, onSelect }: RowProps) {
  const [optimisticOn, setOptimisticOn] = useState<boolean | null>(null);

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
  // Если optimisticOn задан — показываем его, иначе реальное значение из props
  const displayOn = optimisticOn !== null ? optimisticOn : isOn;

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

      <td className="table__td table__td--center table__td--controls">
        <span
          className="toggle-wrap"
          onClick={(e) => {
            const wrap = e.currentTarget;
            if (wrap.classList.contains('toggle-wrap--waiting')) return;
            wrap.classList.add('toggle-wrap--waiting');
            setOptimisticOn(!isOn);
            setTimeout(() => {
              wrap.classList.remove('toggle-wrap--waiting');
              setOptimisticOn(null);
            }, 500);
            onControl(task);
          }}
        >
          <button
            className={`toggle${displayOn ? ' toggle--on' : ''}`}
            title={displayOn ? 'Остановить' : 'Запустить'}
          >
            <span className="toggle__thumb" />
          </button>
        </span>
      </td>

      <td className="table__td table__td--center">{task.task_name}</td>
      <td className="table__td table__td--center">{task.task_group ?? <span className="muted">—</span>}</td>
      <td className="table__td table__td--center">{task.owner}</td>

      <td className="table__td table__td--center">
        <span className={`status-badge ${statusClass}`}>{statusLabel}</span>
      </td>

      <td className="table__td table__td--center">{task.schedule ?? <span className="muted">—</span>}</td>
      <td className="table__td table__td--center">{task.task_deps_id ?? 
        <span className="muted">—</span>}</td>

      <td className="table__td table__td--center">
        <input type="checkbox" checked={task.notifications} readOnly />
      </td>

      <td className="table__td table__td--center">
        <button className="link-btn">Открыть</button>
      </td>

      <td className="table__td">{task.comment ?? <span className="muted">—</span>}</td>
    </tr>
  );
}
