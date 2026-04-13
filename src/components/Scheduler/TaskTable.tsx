import { useState } from 'react';
import type { TaskOut, ServerMessage } from '../../types';
import { startTask, stopTask, oneTimeRun, getTasks, updateTask, parseApiError } from '../../services/api';
import { Play, Pencil, Settings, Check, X } from 'lucide-react';
import './TaskTable.css';

interface Props {
  tasks: TaskOut[];
  selectedId: number | null;
  editingId: number | null;
  setEditingId: (id: number | null) => void;
  onSelect: (id: number | null) => void;
  onRefresh: () => void;
  onServerMessage: (msg: ServerMessage) => void;
}

type SortKey = keyof TaskOut;
type SortDir = 'asc' | 'desc';

export default function TaskTable({ tasks, selectedId, editingId, setEditingId, onSelect, onServerMessage }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('task_id');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

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
    return a.task_id - b.task_id;
  });

  async function handleOneTimeRun(taskId: number) {
    try {
      const { status } = await oneTimeRun(taskId);
      onServerMessage({ status, text: `Задача #${taskId} запущена разово`, ok: true });
    } catch (e) {
      const { status, detail } = parseApiError(e);
      onServerMessage({ status, text: 'Ошибка запуска', detail, ok: false });
    }
  }

  async function handleEdit(taskId: number): Promise<void> {
    try {
      await getTasks();
    } catch (e) {
      const { status, detail } = parseApiError(e);
      onServerMessage({ status, text: 'Ошибка загрузки', detail, ok: false });
    }
  }

  function handleCancel(taskId: number): void {
    setEditingId(null);
  }

  async function handleSave(task: TaskOut): Promise<boolean> {
    try {
      const { status } = await updateTask(task.task_id, task);
      onServerMessage({ status, text: `Задача #${task.task_id} сохранена`, ok: true });
      return true;
    } catch (e) {
      const { status, detail } = parseApiError(e);
      onServerMessage({ status, text: 'Ошибка сохранения', detail, ok: false });
      return false;
    }
  }

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
            <ColHeader label="Управление" col="on_control" />
            <ColHeader label="Имя задачи" col="task_name" />
            <ColHeader label="Группа" col="task_group" />
            <ColHeader label="Владелец" col="owner" />
            <ColHeader label="Статус" col="status" />
            <ColHeader label="Расписание" col="schedule" />
            <ColHeader label="След. запуск" col="schedule" />
            <ColHeader label="Посл. запуск" col="last_run_at" />
            <ColHeader label="Связь с ID" col="task_deps_id" />
            <ColHeader label="Уведомл." col="notifications" />
            <th className="table__th">Логи</th>
            <th className="table__th">Комментарий</th>
            <th className="table__th">Системные</th>
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
                isSelected={selectedId === task.task_id}
                editingId={editingId}
                setEditingId={setEditingId}
                onControl={handleControl}
                onOneTimeRun={handleOneTimeRun}
                onEdit={handleEdit}
                onSave={handleSave}
                onCancel={handleCancel}
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
  isSelected: boolean;
  editingId: number | null;
  setEditingId: (id: number | null) => void;
  onControl: (task: TaskOut) => void;
  onOneTimeRun: (taskId: number) => void;
  onEdit: (taskId: number) => Promise<void>;
  onSave: (task: TaskOut) => Promise<boolean>;
  onCancel: (taskId: number) => void;
  onSelect: (id: number | null) => void;
}

function TaskRow({ task, isSelected, editingId, setEditingId, onControl, onOneTimeRun, onEdit, onSave, onCancel, onSelect }: RowProps) {
  const [optimisticOn, setOptimisticOn] = useState<boolean | null>(null);
  const isEditing = editingId === task.task_id;
  const isLocked = editingId !== null && !isEditing;

  const statusClass =
    new Date(task.run_expire_at) >= new Date() ? 'status--running'
    : task.status === 'active' ? 'status--active'
    : task.status === 'running'   ? 'status--running'
    : task.status === 'error' ? 'status--error'
    : 'status--stopped';

  const statusLabel =
    task.status === 'running' ? 'Running'
    : task.status === 'error' ? 'Ошибка'
    : task.status === 'stopped' ? 'Остановлен'
    : new Date(task.run_expire_at) >= new Date() ? 'Running'
    : task.status;

  const isOn = task.on_control === 'on';
  const displayOn = optimisticOn !== null ? optimisticOn : isOn;

  function handleRowClick(e: React.MouseEvent) {
    if (isLocked) return;
    if ((e.target as HTMLElement).closest('button, input, a')) return;
    onSelect(isSelected ? null : task.task_id);
  }

  return (
    <tr
      className={[
        'table__row',
        isSelected ? 'table__row--selected' : '',
        isLocked ? 'table__row--locked' : '',
      ].filter(Boolean).join(' ')}
      onClick={handleRowClick}
    >
      <td className="table__td table__td--id">{task.task_id}</td>

      <td className="table__td table__td--center table__td--controls">
        <span
          className="toggle-wrap"
          onClick={() => {
            if (isLocked || optimisticOn !== null) return;
            setOptimisticOn(!isOn);
            setTimeout(() => {
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
      <td className="table__td table__td--center">{task.task_group ?? <span className="muted"></span>}</td>
      <td className="table__td table__td--center">{task.owner}</td>

      <td className="table__td table__td--center">
        <span className={`status-badge ${statusClass}`}>{statusLabel}</span>
      </td>

      <td className="table__td table__td--center">{task.schedule ?? <span className="muted"></span>}</td>
      <td className="table__td table__td--center">{task.next_run_at ?? <span className="muted"></span>}</td>
      <td className="table__td table__td--center">{task.last_run_at 
        ? task.last_run_at.replace('T', ' ').slice(0, 19) 
        : <span className="muted"></span>}
      </td>
      <td className="table__td table__td--center">{task.task_deps_id ?? 
        <span className="muted"></span>}</td>

      <td className="table__td table__td--center">
        <input type="checkbox" checked={task.notifications} readOnly />
      </td>

      <td className="table__td table__td--center">
        <button className="link-btn">Открыть</button>
      </td>

      <td className="table__td">{task.comment ?? <span className="muted"></span>}</td>
      <td className="table__td table__td--center">
        <div className="action-btns">
          {isEditing ? (
            <>
              <button
                className="run-btn run-btn--save"
                title="Сохранить"
                onClick={async () => {
                  const ok = await onSave(task);
                  if (ok) setEditingId(null);
                }}
              >
                <Check size={11} strokeWidth={2.5} />
              </button>
              <button
                className="run-btn run-btn--cancel"
                title="Отмена"
                onClick={() => onCancel(task.task_id)}
              >
                <X size={11} strokeWidth={2.5} />
              </button>
            </>
          ) : (
            <>
              <button className="run-btn run-btn--launch" title="Разовый запуск" disabled={isLocked} onClick={() => onOneTimeRun(task.task_id)}>
                <Play size={9} strokeWidth={2} />
              </button>
              <button
                className="run-btn run-btn--edit"
                title="Редактировать"
                disabled={isLocked}
                onClick={async () => {
                  onSelect(task.task_id);
                  setEditingId(task.task_id);
                  await onEdit(task.task_id);
                }}
              >
                <Pencil size={11} strokeWidth={1.8} />
              </button>
            </>
          )}
          <button className="run-btn run-btn--settings" title="Настройки" disabled={isLocked}>
            <Settings size={11} strokeWidth={1.8} />
          </button>
        </div>
      </td>
    </tr>
  );
}
