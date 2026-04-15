import { useEffect, useState } from 'react';
import type { TaskOut, TaskPropsOut, TaskType, ConnectionOut } from '../../types';
import { Pencil, Check, X } from 'lucide-react';
import { getConnections } from '../../services/api';
import './TaskPropsModal.css';

interface Props {
  task: TaskOut;
  props: TaskPropsOut;
  isEditing: boolean;
  onClose: () => void;
  onEdit: () => void;
  onCancelEdit: () => void;
  onSaveProp: (formData: FormData) => Promise<void>;
}

type PropEditState = {
  task_type: TaskType;
  connection_id: number | null;
  from_dt: string;
  until_dt: string;
  cron_expression: string;
  email: string;
  tg_chat_id: string;
  root_folder: string;
  files: File[];
};

const TASK_TYPES: TaskType[] = ['sql', 'python', 'bat'];

function toDateInput(dt: string | null): string {
  if (!dt) return '';
  // datetime-local expects "YYYY-MM-DDTHH:MM"
  return dt.slice(0, 16);
}

function Row({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div className="props-modal__row">
      <span className="props-modal__label">{label}</span>
      {value
        ? <span className="props-modal__value">{value}</span>
        : <span className="props-modal__value props-modal__value--muted">—</span>}
    </div>
  );
}

function EditRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="props-modal__row">
      <span className="props-modal__label">{label}</span>
      <div className="props-modal__edit-field">{children}</div>
    </div>
  );
}

function Divider({ label }: { label: string }) {
  return <div className="props-modal__divider">{label}</div>;
}

export default function TaskPropsModal({ task, props, isEditing, onClose, onEdit, onCancelEdit, onSaveProp }: Props) {
  const hasDep = task.task_deps_id !== null;
  const [saving, setSaving] = useState(false);
  const [connections, setConnections] = useState<ConnectionOut[]>([]);
  const [editState, setEditState] = useState<PropEditState>({
    task_type: props.task_type,
    connection_id: props.connection_id,
    from_dt: toDateInput(props.from_dt),
    until_dt: toDateInput(props.until_dt),
    cron_expression: props.cron_expression ?? '',
    email: props.email ?? '',
    tg_chat_id: props.tg_chat_id ?? '',
    root_folder: props.storage_path ?? '',
    files: [],
  });

  useEffect(() => {
    if (isEditing) {
      getConnections().then(({ data }) => setConnections(data)).catch(() => {});
      setEditState({
        task_type: props.task_type,
        connection_id: props.connection_id,
        from_dt: toDateInput(props.from_dt),
        until_dt: toDateInput(props.until_dt),
        cron_expression: props.cron_expression ?? '',
        email: props.email ?? '',
        tg_chat_id: props.tg_chat_id ?? '',
        root_folder: props.storage_path ?? '',
        files: [],
      });
    }
  }, [isEditing]);

  function set<K extends keyof PropEditState>(key: K, value: PropEditState[K]) {
    setEditState(s => ({ ...s, [key]: value }));
  }

  async function handleSave() {
    setSaving(true);
    try {
      const fd = new FormData();
      fd.append('task_id', String(task.task_id));
      fd.append('task_type', editState.task_type);
      if (editState.connection_id !== null) fd.append('connection_id', String(editState.connection_id));
      if (editState.from_dt) fd.append('from_dt', editState.from_dt);
      if (editState.until_dt) fd.append('until_dt', editState.until_dt);
      if (editState.cron_expression) fd.append('cron_expression', editState.cron_expression);
      if (editState.email) fd.append('email', editState.email);
      if (editState.tg_chat_id) fd.append('tg_chat_id', editState.tg_chat_id);
      fd.append('root_folder', editState.root_folder);
      if (editState.files.length > 0) {
        editState.files.forEach(f => fd.append('files', f));
      }
      await onSaveProp(fd);
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [onClose]);

  return (
    <div className="props-overlay">
      <div className="props-modal" onClick={e => e.stopPropagation()}>

        <div className="props-modal__header">
          <span className="props-modal__title">
            Задача #{task.task_id} — {task.task_name}
          </span>
          <button className="props-modal__close" onClick={onClose}>✕</button>
        </div>

        <div className="props-modal__body">

          <div className="props-modal__left">

            <div className="props-modal__section">
              {isEditing ? (
                <>
                  <EditRow label="Тип">
                    <select className="props-modal__input" value={editState.task_type}
                      onChange={e => set('task_type', e.target.value as TaskType)}>
                      {TASK_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                  </EditRow>
                  <EditRow label="Подключение">
                    <select className="props-modal__input" value={editState.connection_id ?? ''}
                      onChange={e => set('connection_id', e.target.value === '' ? null : Number(e.target.value))}>
                      <option value="">—</option>
                      {connections.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                  </EditRow>
                </>
              ) : (
                <>
                  <Row label="Тип" value={props.task_type} />
                  <Row label="Подключение" value={props.conn_name} />
                </>
              )}
            </div>

            {!hasDep && (
              <div className="props-modal__section">
                <Divider label="Расписание" />
                {isEditing ? (
                  <>
                    <EditRow label="С даты">
                      <input className="props-modal__input" type="datetime-local" value={editState.from_dt}
                        onChange={e => set('from_dt', e.target.value)} />
                    </EditRow>
                    <EditRow label="По дату">
                      <input className="props-modal__input" type="datetime-local" value={editState.until_dt}
                        onChange={e => set('until_dt', e.target.value)} />
                    </EditRow>
                    <EditRow label="Cron">
                      <input className="props-modal__input" type="text" value={editState.cron_expression}
                        onChange={e => set('cron_expression', e.target.value)} />
                    </EditRow>
                  </>
                ) : (
                  <>
                    <Row label="С даты" value={props.from_dt?.replace('T', ' ')} />
                    <Row label="По дату" value={props.until_dt?.replace('T', ' ')} />
                    <Row label="Cron" value={props.cron_expression} />
                  </>
                )}
              </div>
            )}

            <div className="props-modal__section">
              <Divider label="Уведомления" />
              {isEditing ? (
                <>
                  <EditRow label="Email">
                    <input className="props-modal__input" type="text" value={editState.email}
                      onChange={e => set('email', e.target.value)} />
                  </EditRow>
                  <EditRow label="Telegram">
                    <input className="props-modal__input" type="text" value={editState.tg_chat_id}
                      onChange={e => set('tg_chat_id', e.target.value)} />
                  </EditRow>
                </>
              ) : (
                <>
                  <Row label="Email" value={props.email} />
                  <Row label="Telegram" value={props.tg_chat_id} />
                </>
              )}
            </div>

          </div>

          <div className="props-modal__right">
            {isEditing ? (
              <>
                <Divider label="Путь" />
                <EditRow label="">
                  <input className="props-modal__input" type="text"
                    placeholder="Путь к папке на сервере"
                    value={editState.root_folder}
                    onChange={e => set('root_folder', e.target.value)} />
                </EditRow>
                <Divider label="Файлы" />
                <label className="props-modal__file-btn">
                  Выбрать файлы
                  <input type="file" multiple style={{ display: 'none' }}
                    onChange={e => set('files', Array.from(e.target.files ?? []))} />
                </label>
                <div className="props-modal__files">
                  {editState.files.length > 0
                    ? [...editState.files].sort((a, b) => a.name.localeCompare(b.name)).map((f, i) => (
                        <span key={i} className="props-modal__file">
                          <span className="props-modal__file-num">{i + 1}.</span>{f.name}
                        </span>
                      ))
                    : (props.file_names ?? []).length > 0
                      ? [...(props.file_names ?? [])].sort((a, b) => a.localeCompare(b)).map((f, i) => (
                          <span key={i} className="props-modal__file props-modal__file--existing">
                            <span className="props-modal__file-num">{i + 1}.</span>{f}
                          </span>
                        ))
                      : <span className="props-modal__value props-modal__value--muted">Нет файлов</span>
                  }
                </div>
              </>
            ) : (
              <>
                <Divider label="Путь" />
                {props.storage_path && (
                  <span className="props-modal__path">{props.storage_path}</span>
                )}
                <Divider label="Файлы" />
                <div className="props-modal__files">
                  {(props.file_names ?? []).length > 0
                    ? [...(props.file_names ?? [])].sort((a, b) => a.localeCompare(b)).map((f, i) => (
                        <span key={i} className="props-modal__file">
                          <span className="props-modal__file-num">{i + 1}.</span>{f}
                        </span>
                      ))
                    : <span className="props-modal__value props-modal__value--muted">Нет файлов</span>
                  }
                </div>
              </>
            )}
          </div>

        </div>

        <div className="props-modal__footer">
          {isEditing ? (
            <>
              <button className="props-modal__btn props-modal__btn--save" onClick={handleSave} disabled={saving}>
                <Check size={13} strokeWidth={2.5} />
                {saving ? 'Сохранение...' : 'Сохранить'}
              </button>
              <button className="props-modal__btn props-modal__btn--cancel" onClick={onCancelEdit}>
                <X size={13} strokeWidth={2.5} />
                Отмена
              </button>
            </>
          ) : (
            <>
              <button className="props-modal__btn props-modal__btn--pencil" title="Редактировать"
                onClick={onEdit}>
                <Pencil size={13} strokeWidth={1.8} />
              </button>
              <button className="props-modal__btn props-modal__btn--ok" onClick={onClose}>
                OK
              </button>
            </>
          )}
        </div>

      </div>
    </div>
  );
}
