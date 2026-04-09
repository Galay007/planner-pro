import { useState, useEffect } from 'react';
import type { ConnType, ConnectionIn } from '../../types';
import { createConnection, testConnection, parseApiError } from '../../services/api';
import type { ServerMessage } from '../../types';
import './AddConnectionModal.css';

const CONN_TYPES: ConnType[] = ['postgresql', 'mysql', 'mariadb', 'mssql', 'oracle', 'sqlite', 'teradata'];

interface Props {
  onClose: () => void;
  onSaved: () => void;
  pushMessage: (msg: ServerMessage) => void;
}

type FormState = Omit<ConnectionIn, 'port'> & { port: number | '' | null };

const defaultForm = (): FormState => ({
  name: '',
  conn_type: 'postgresql',
  host: '',
  port: '',
  db_name: '',
  login: '',
  pass_str: '',
  db_path: null,
});

function toPayload(f: FormState): ConnectionIn {
  return {
    ...f,
    port: (f.port === '' || f.port === null) ? null : f.port,
    host: f.host || null,
    db_name: f.db_name || null,
    login: f.login || null,
    pass_str: f.pass_str || null,
    db_path: f.db_path || null,
  };
}

export default function AddConnectionModal({ onClose, onSaved, pushMessage }: Props) {
  const [form, setForm] = useState<FormState>(defaultForm());
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testPassed, setTestPassed] = useState<boolean | null>(null);

  const isSqlite = form.conn_type === 'sqlite';

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
      if (e.key === 'Enter' && !saving && !testing) handleSave();
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [onClose, saving, testing, form]);

  const [touched, setTouched] = useState<Partial<Record<keyof FormState, boolean>>>({});

  function isFieldInvalid(field: keyof FormState) {
    return touched[field] && !form[field];
  }

  function touchRequired() {
    const fields: (keyof FormState)[] = isSqlite
      ? ['name', 'db_path']
      : ['name', 'host', 'port', 'db_name', 'login', 'pass_str'];
    const next: Partial<Record<keyof FormState, boolean>> = {};
    fields.forEach((f) => (next[f] = true));
    setTouched(next);
    return fields.every((f) => !!form[f]);
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    const { name, value } = e.target;
    const cleaned = name === 'db_path' ? value.replace(/['"]/g, '') : value;
    setForm((prev) => ({ ...prev, [name]: cleaned }));
    setTestPassed(null);
  }

  function handlePortChange(e: React.ChangeEvent<HTMLInputElement>) {
    const val = e.target.value;
    setForm((prev) => ({ ...prev, port: val === '' ? '' : parseInt(val, 10) }));
    setTestPassed(false);
  }

  function handleTypeChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const conn_type = e.target.value as ConnType;
    const isSql = conn_type === 'sqlite';
    setForm({
      ...defaultForm(),
      conn_type,
      name: form.name,
      ...(isSql
        ? { host: null, port: null, db_name: null, login: null, pass_str: null, db_path: '' }
        : { db_path: null }),
    });
    setTouched({});
  }

  async function runTest(): Promise<boolean> {
    setTesting(true);
    try {
      const result = await testConnection(toPayload(form));
      const ok = result.status === 200;
      pushMessage({ status: result.status, text: 'Тест соединения', detail: result.detail, ok });
      setTestPassed(ok);
      return ok;
    } catch (e) {
      const err = parseApiError(e);
      pushMessage({ status: err.status, text: 'Ошибка теста', detail: err.detail, ok: false });
      setTestPassed(false);  // false = тест запущен, провален
      return false;
    } finally {
      setTesting(false);
    }
  }

  async function handleTest() {
    if (!touchRequired()) return;
    await runTest();
  }

  async function handleSave() {
    if (!touchRequired()) return;
    const testOk = await runTest();
    if (!testOk) return;
    setSaving(true);
    try {
      const result = await createConnection(toPayload(form));
      if (result.status === 200 || result.status === 201) {
        pushMessage({ status: result.status, text: 'Подключение создано', detail: result.detail, ok: true });
        onSaved();
      } else {
        pushMessage({ status: result.status, text: 'Ошибка сохранения', detail: result.detail, ok: false });
      }
    } catch (e) {
      const err = parseApiError(e);
      pushMessage({ status: err.status, text: 'Ошибка сохранения', detail: err.detail, ok: false });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal">
        <div className="modal__header">
          <span className="modal__title">Новое подключение</span>
        </div>

        <div className="modal__body">
          <div className="modal__field">
            <label className="modal__label">Тип СУБД</label>
            <select className="modal__select" name="conn_type" value={form.conn_type} onChange={handleTypeChange}>
              {CONN_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          <div className="modal__field">
            <label className="modal__label">Имя подключения <span className="modal__required">*</span></label>
            <input className={`modal__input${isFieldInvalid('name') ? ' modal__input--error' : ''}`} name="name" value={form.name} onChange={handleChange} placeholder="my_connection" />
          </div>

          {!isSqlite && (
            <>
              <div className="modal__field">
                <label className="modal__label">Хост <span className="modal__required">*</span></label>
                <input className={`modal__input${isFieldInvalid('host') ? ' modal__input--error' : ''}`} name="host" value={form.host ?? ''} onChange={handleChange} placeholder="localhost" />
              </div>
              <div className="modal__field">
                <label className="modal__label">Порт <span className="modal__required">*</span></label>
                <input className={`modal__input${isFieldInvalid('port') ? ' modal__input--error' : ''}`} name="port" type="number" value={form.port ?? ''} onChange={handlePortChange} placeholder="5432" />
              </div>
              <div className="modal__field">
                <label className="modal__label">База данных <span className="modal__required">*</span></label>
                <input className={`modal__input${isFieldInvalid('db_name') ? ' modal__input--error' : ''}`} name="db_name" value={form.db_name ?? ''} onChange={handleChange} placeholder="mydb" />
              </div>
              <div className="modal__field">
                <label className="modal__label">Логин <span className="modal__required">*</span></label>
                <input className={`modal__input${isFieldInvalid('login') ? ' modal__input--error' : ''}`} name="login" value={form.login ?? ''} onChange={handleChange} placeholder="user" />
              </div>
              <div className="modal__field">
                <label className="modal__label">Пароль <span className="modal__required">*</span></label>
                <input className={`modal__input${isFieldInvalid('pass_str') ? ' modal__input--error' : ''}`} name="pass_str" type="password" value={form.pass_str ?? ''} onChange={handleChange} placeholder="••••••" />
              </div>
            </>
          )}

          {isSqlite && (
            <div className="modal__field">
              <label className="modal__label">Путь к файлу <span className="modal__required">*</span></label>
              <input className={`modal__input${isFieldInvalid('db_path') ? ' modal__input--error' : ''}`} name="db_path" value={form.db_path ?? ''} onChange={handleChange} placeholder="/path/to/db.sqlite" />
            </div>
          )}
        </div>

        <div className="modal__footer">
          <button className="modal__btn modal__btn--save" onClick={handleSave} disabled={saving}>
            Сохранить
          </button>
          <button
            className={`modal__btn modal__btn--test${testPassed === true ? ' modal__btn--test-ok' : testPassed === false ? ' modal__btn--test-fail' : ''}`}
            onClick={handleTest}
            disabled={testing}
          >
            {testPassed === true ? 'OK' : testPassed === false ? 'Failed' : 'Тест'}
          </button>
          <button className="modal__btn modal__btn--cancel" onClick={onClose}>Отмена</button>
        </div>
      </div>
    </div>
  );
}
