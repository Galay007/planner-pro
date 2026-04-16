import { useState, useRef, useEffect } from 'react';
import type { TaskOut, TaskPropsOut, ServerMessage } from '../../types';
import { startTask, stopTask, oneTimeRun, getTasks,
  saveTask, parseApiError, startEdit, cancelEdit, sendHeartBeat, getProp, createProp, saveProp } from '../../services/api';
import { Play, Pencil, Settings, Check, X } from 'lucide-react';
import TaskPropsModal from './TaskPropsModal';
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

type EditState = {
  task_name: string;
  task_group: string | null;
  owner: string;
  task_deps_id: number | null;
  notifications: boolean;
  comment: string | null;
};

const EDITABLE_FIELDS: (keyof EditState)[] = [
  'task_name', 'task_group', 'owner', 'task_deps_id', 'notifications', 'comment',
];

export default function TaskTable({ tasks, selectedId, editingId,
  setEditingId, onSelect, onServerMessage }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('task_id');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const [propsModal, setPropsModal] = useState<{ task: TaskOut; props: TaskPropsOut; isNew: boolean } | null>(null);
  const hasChangesRef = useRef<() => boolean>(() => false);

  const emptyProps = (task: TaskOut): TaskPropsOut => ({
    task_id: task.task_id,
    task_type: 'sql',
    connection_id: null,
    conn_name: null,
    from_dt: null,
    until_dt: null,
    cron_expression: null,
    storage_path: '',
    file_names: null,
    email: null,
    tg_chat_id: null,
  });

  async function handleSettings(task: TaskOut) {
    try {
      const { data } = await getProp(task.task_id);
      setPropsModal({ task, props: data, isNew: false });
    } catch (e) {
      const { status } = parseApiError(e);
      if (status === 404) {
        setPropsModal({ task, props: emptyProps(task), isNew: true });
      } else {
        const { detail } = parseApiError(e);
        onServerMessage({ status, text: 'Ошибка загрузки настроек', detail, ok: false });
      }
    }
  }

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

  useEffect(() => {
    if (editingId === null) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && !hasChangesRef.current()) void handleCancel(editingId!);
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [editingId]);

  async function handleOneTimeRun(taskId: number) {
    try {
      const { status } = await oneTimeRun(taskId);
      onServerMessage({ status, text: `Задача #${taskId} запущена разово`, ok: true });
    } catch (e) {
      const { status, detail } = parseApiError(e);
      onServerMessage({ status, text: 'Ошибка запуска', detail, ok: false });
    }
  }

  async function handleCancel(taskId: number) {
    try {
      const { status } = await cancelEdit(taskId);
      onServerMessage({ status, text: `Задача #${taskId} редактир. остановлено`, ok: true });
      stopEditing()
    } catch (e) {
      const { status, detail } = parseApiError(e);
      onServerMessage({ status, text: 'Ошибка запуска', detail, ok: false });
    }
  }

  async function handleSave(edited: TaskOut) {
    const original = tasks.find(t => t.task_id === edited.task_id);
    const hasChanges = !original || EDITABLE_FIELDS.some(f => original[f] !== edited[f]);
    if (!hasChanges) { handleCancel(edited.task_id); return; }
    try {
      const { status } = await saveTask(edited.task_id, edited);
      onServerMessage({ status, text: `Задача #${edited.task_id} сохранена`, ok: true });
      stopEditing();
    } catch (e) {
      const { status, detail } = parseApiError(e);
      onServerMessage({ status, text: 'Ошибка сохранения', detail, ok: false });
    }
  }
  
  const timerRef = useRef<number | null>(null);
  const editingTaskIdRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current !== null) {
        clearInterval(timerRef.current);
        console.log("Timer stoped")
      }
      if (editingTaskIdRef.current !== null) {
        void cancelEdit(editingTaskIdRef.current);
      }
    };
  }, []);

  async function handleEdit(task: TaskOut) {
    try {
      await getTasks();
      const { status } = await startEdit(task.task_id);
      onServerMessage({ status, text: `Задача #${task.task_id} редакт. начато`, ok: true });
      setEditingId(task.task_id);
      editingTaskIdRef.current = task.task_id;
      const intervalMs = Math.max(1, task.TTL_EDIT_SECONDS - 5) * 1000;

      timerRef.current = window.setInterval(() => {
        void handleHeartBeat(task);
      }, intervalMs);

    } catch (e) {
      const { status, detail } = parseApiError(e);
      onServerMessage({ status, text: 'Ошибка запуска', detail, ok: false });
      stopEditing();
    }
  }

  async function handleHeartBeat(task: TaskOut) {
    try {
      const { status } = await sendHeartBeat(task.task_id);
      onServerMessage({ status, text: `Задача #${task.task_id} отправлен hearbeat`, ok: true });
    } catch (e) {
      const { status, detail } = parseApiError(e);
      onServerMessage({ status, text: 'Ошибка heartbeat', detail, ok: false });
      stopEditing();
    }
  }

  function stopEditing() {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
      console.log("Timer stoped")
    }
    editingTaskIdRef.current = null;
    setEditingId(null);
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
    <>
    <div className="table-wrap">
      <table className="task-table">
        <thead>
          <tr>
            <ColHeader label="ID" col="task_id" />
            <ColHeader label="Пуск" col="on_control" />
            <ColHeader label="Имя задачи" col="task_name" />
            <ColHeader label="Группа" col="task_group" />
            <ColHeader label="Владелец" col="owner" />
            <ColHeader label="Статус" col="status" />
            <ColHeader label="Расписание" col="schedule_cron" />
            <ColHeader label="След. запуск" col="next_run_at" />
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
                hasChangesRef={hasChangesRef}
                availableDepsIds={tasks
                                  .filter(t => t.task_id !== task.task_id)
                                  .map(t => t.task_id)
                                  .sort((a, b) => a - b)}
                onControl={handleControl}
                onOneTimeRun={handleOneTimeRun}
                onEdit={handleEdit}
                onSaveTask={handleSave}
                onCancel={handleCancel}
                onSelect={onSelect}
                onSettings={handleSettings}
              />
            ))
          )}
        </tbody>
      </table>
    </div>

      {propsModal && (
        <TaskPropsModal
          task={propsModal.task}
          props={propsModal.props}
          onClose={() => setPropsModal(null)}
          isEditing={editingId === propsModal.task.task_id}
          onEdit={() => { onSelect(propsModal.task.task_id); setEditingId(propsModal.task.task_id); void handleEdit(propsModal.task); }}
          onCancelEdit={() => {
            if (!hasChangesRef.current()) void handleCancel(propsModal.task.task_id);
          }}
          onSaveProp={async (formData) => {
            const { status } = propsModal.isNew
              ? await createProp(formData)
              : await saveProp(propsModal.task.task_id, formData);
            onServerMessage({ status, text: `Настройки задачи #${propsModal.task.task_id} сохранены`, ok: true });
            if (!hasChangesRef.current()) void handleCancel(propsModal.task.task_id);
            setPropsModal(null);
          }}
        />
      )}
    </>
  );
}

interface RowProps {
  task: TaskOut;
  isSelected: boolean;
  editingId: number | null;
  availableDepsIds: number[];
  hasChangesRef: { current: () => boolean };
  onControl: (task: TaskOut) => void;
  onOneTimeRun: (taskId: number) => void;
  onEdit: (task: TaskOut) => void;
  onSaveTask: (task: TaskOut) => void;
  onCancel: (taskId: number) => void;
  onSelect: (id: number | null) => void;
  onSettings: (task: TaskOut) => void;
}

function TaskRow({ task, isSelected, editingId, availableDepsIds, hasChangesRef, onControl, onOneTimeRun, onEdit, onSaveTask, onCancel, onSelect, onSettings }: RowProps) {
  const [optimisticOn, setOptimisticOn] = useState<boolean | null>(null);
  const isEditing = editingId === task.task_id;
  const isLocked = editingId !== null && !isEditing;

  const [editState, setEditState] = useState<EditState>({
    task_name: task.task_name,
    task_group: task.task_group,
    owner: task.owner,
    task_deps_id: task.task_deps_id,
    notifications: task.notifications,
    comment: task.comment,
  });

  useEffect(() => {
    if (isEditing) {
      setEditState({
        task_name: task.task_name,
        task_group: task.task_group,
        owner: task.owner,
        task_deps_id: task.task_deps_id,
        notifications: task.notifications,
        comment: task.comment,
      });
    }
  }, [isEditing]);

  useEffect(() => {
    if (isEditing) {
      hasChangesRef.current = () =>
        EDITABLE_FIELDS.some(f => task[f] !== editState[f]);
    }
  }, [isEditing, editState]);

  const statusClass =
    new Date(task.run_expire_at) >= new Date() ? 'status--running'
    : new Date(task.edit_expire_at) >= new Date() ? 'status--editing'
    : task.status === 'active' ? 'status--active'
    : task.status === 'running'   ? 'status--running'
    : task.status === 'error' ? 'status--error'
    : 'status--stopped';

const statusLabel =
    new Date(task.run_expire_at) >= new Date() ? 'Running'
    : new Date(task.edit_expire_at) >= new Date() ? 'Editing'
    : task.status === 'running' ? 'Running'
    : task.status === 'error' ? 'Ошибка'
    : task.status === 'active' ? 'Active'
    : task.status === 'not active' ? 'No active'
    : task.status;

  const isOn = task.on_control === 'on';
  const displayOn = optimisticOn !== null ? optimisticOn : isOn;

  function handleRowClick(e: React.MouseEvent) {
    if (isLocked) return;
    if ((e.target as HTMLElement).closest('button, input, a')) return;
    onSelect(task.task_id);
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

      <td className="table__td table__td--name">
        {isEditing
          ? <input className="edit-input edit-input--name" 
                value={editState.task_name} 
                onChange={e => setEditState(s => ({ ...s, task_name: e.target.value }))} />
          : task.task_name}
      </td>
      <td className="table__td table__td--center">
        {isEditing
          ? <input className="edit-input edit-input--group" value={editState.task_group ?? ''} onChange={e => setEditState(s => ({ ...s, task_group: e.target.value || null }))} />
          : (task.task_group ?? <span className="muted"></span>)}
      </td>
      <td className="table__td table__td--center">
        {isEditing
          ? <input className="edit-input edit-input--owner" 
          value={editState.owner} onChange={e => setEditState(s => ({ ...s, owner: e.target.value }))} />
          : task.owner}
      </td>

      <td className="table__td table__td--center">
        <span className={`status-badge ${statusClass}`}>{statusLabel}</span>
      </td>

      <td className="table__td table__td--center">{task.schedule_cron ?? task.schedule_depend ?? <span className="muted"></span>}</td>
      <td className="table__td table__td--center">{task.next_run_at 
       ? (() => { const [d, t] = task.next_run_at!.split(' '); const [day, mon, yr] = d.split('.'); return `${day}.${mon}.${yr.slice(2)} ${t.slice(0, 5)}`; })()
        : <span className="muted"></span>}
        </td>
      <td className="table__td table__td--center">{task.last_run_at 
        ? (() => { const [d, t] = task.last_run_at!.replace('T', ' ').split(' '); const [yr, mon, day] = d.split('-'); return `${day}.${mon}.${yr.slice(2)} ${t.slice(0, 5)}`; })()
        : <span className="muted"></span>}
      </td>
      <td className="table__td table__td--center">
        {isEditing
          ? (
            <>
              <select className="edit-select"
                value={editState.task_deps_id ?? ''}
                onChange={e => setEditState(s => ({ ...s, task_deps_id: e.target.value === ''
                ? null : Number(e.target.value) }))}>
                <option value="">пусто</option>
                {availableDepsIds.map(id => <option key={id} value={id}>{id}</option>)}
              </select>
              {editState.task_deps_id !== null && task.schedule_cron !== null && (
                <div className="edit-warning">Cron {task.schedule_cron} будет удалён!</div>
              )}
            </>
          )
          : (task.task_deps_id ?? <span className="muted"></span>)}
      </td>

      <td className="table__td table__td--center">
        <input
          className="custom-checkbox"
          type="checkbox"
          checked={isEditing ? editState.notifications : task.notifications}
          readOnly={!isEditing}
          onChange={isEditing ? e =>
            setEditState(s => ({ ...s, notifications: e.target.checked })) : undefined}
        />
      </td>

      <td className="table__td table__td--center">
        <button className="link-btn">Открыть</button>
      </td>

      <td className="table__td table__td--center">
        {isEditing
          ? <input className="edit-input edit-input--comment" value={editState.comment ?? ''} 
            onChange={e => setEditState(s => ({ ...s, comment: e.target.value || null }))} />
          : (task.comment ?? <span className="muted"></span>)}
      </td>
      <td className="table__td table__td--center">
        <div className="action-btns">
          {isEditing ? (
            <>
              <button
                className="run-btn run-btn--save"
                title="Сохранить"
                onClick={() => onSaveTask({ ...task, ...editState })}
              >
                <Check size={11} strokeWidth={2.5} />
              </button>
              <button
                className="run-btn run-btn--cancel"
                title="Отмена"
                onClick={async () => {onCancel(task.task_id);
                }}
              >
                <X size={11} strokeWidth={2.5} />
              </button>
            </>
          ) : (
            <>
              <button className="run-btn run-btn--launch" 
                title="Разовый запуск" disabled={isLocked} 
                onClick={() => onOneTimeRun(task.task_id)}>
                <Play size={9} strokeWidth={2} />
              </button>
              <button
                className="run-btn run-btn--edit"
                title="Редактировать"
                disabled={isLocked}
                onClick={async () => {
                  onSelect(task.task_id);
                  onEdit(task); 
                }}
              >
                <Pencil size={11} strokeWidth={1.8} />
              </button>
            </>
          )}
          <button className="run-btn run-btn--settings" title="Настройки" disabled={isLocked}
            onClick={() => onSettings(task)}>
            <Settings size={11.5} strokeWidth={1.8} />
          </button>
        </div>
      </td>
    </tr>
  );
}
