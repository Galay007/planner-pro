import { useState, useEffect, useCallback, useRef } from 'react';
import type { ConnectionOut, ServerMessage } from '../../types';
import {
  getConnections, deleteConnection,
  testConnection, parseApiError,
} from '../../services/api';
import ConnectionsToolbar from './ConnectionsToolbar';
import ConnectionsList from './ConnectionsList';
import ConnectionDetail from './ConnectionDetail';
import AddConnectionModal from './AddConnectionModal';
import './ConnectionsPage.css';

export default function ConnectionsPage() {
  const [connections, setConnections] = useState<ConnectionOut[]>([]);
  const [selectedName, setSelectedName] = useState<string | null>(null);
  const [detail, setDetail] = useState<ConnectionOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testPassed, setTestPassed] = useState<boolean | null>(null);
  const [search, setSearch] = useState('');
  const [serverMessage, setServerMessage] = useState<ServerMessage | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const msgTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  function pushMessage(msg: ServerMessage) {
    setServerMessage(msg);
    if (msgTimer.current) clearTimeout(msgTimer.current);
    msgTimer.current = setTimeout(() => setServerMessage(null), 5000);
  }

  const fetchNames = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    else setRefreshing(true);
    try {
      const result = await getConnections();
      setConnections(result.data);
    } catch (e) {
      const err = parseApiError(e);
      pushMessage({ status: err.status, text: 'Ошибка загрузки', detail: err.detail, ok: false });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchNames();
  }, [fetchNames]);

  useEffect(() => {
    const busy = loading || refreshing || deleting || testing;
    document.body.classList.toggle('is-loading', busy);
  }, [loading, refreshing, deleting, testing]);

  function handleSelect(name: string) {
    setSelectedName(name);
    setDetail(connections.find((c) => c.name === name) ?? null);
    setTestPassed(null);
  }

  async function handleDelete() {
    if (!selectedName) return;
    setDeleting(true);
    try {
      const result = await deleteConnection(selectedName);
      pushMessage({ status: result.status, text: `Удалено: ${selectedName}`, detail: result.detail, ok: result.status === 200 });
      setSelectedName(null);
      setDetail(null);
      await fetchNames(true);
    } catch (e) {
      const err = parseApiError(e);
      pushMessage({ status: err.status, text: 'Ошибка удаления', detail: err.detail, ok: false });
    } finally {
      setDeleting(false);
    }
  }

  async function handleTest() {
    if (!selectedName || !detail) return;
    setTesting(true);
    try {
      const result = await testConnection(detail);
      const ok = result.status === 200;
      pushMessage({ status: result.status, text: `Тест: ${selectedName}`, detail: result.detail, ok });
      setTestPassed(ok);
    } catch (e) {
      const err = parseApiError(e);
      pushMessage({ status: err.status, text: 'Ошибка теста', detail: err.detail, ok: false })
      setTestPassed(false);
    } finally {
      setTesting(false);
    }
  }

  function handleSaved() {
    setShowAddModal(false);
    fetchNames(true);
  }

  return (
    <div className="connections">
            <div className="connections__header">
        <h1 className="connections__title">Подключения к БД</h1>
      </div>

      <ConnectionsToolbar
        onAdd={() => setShowAddModal(true)}
        onDelete={handleDelete}
        onTest={handleTest}
        onRefresh={() => fetchNames(true)}
        selectedName={selectedName}
        deleting={deleting}
        testing={testing}
        refreshing={refreshing}
      />

      <div className="connections__search-bar">
        <div className="search-input-wrap">
          <span className="search-icon">🔍</span>
          <input
            className="search-input"
            placeholder="Поиск…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        {search && (
          <button className="btn-reset" onClick={() => setSearch('')}>Сбросить</button>
        )}
        {serverMessage && testPassed !== false && (
          <div className={`server-msg server-msg--${serverMessage.ok ? '' : 'err'}`}>
            {/* <span className="server-msg__status">{serverMessage.status}</span>
            <span className="server-msg__text">{serverMessage.text}</span> */}
            {!serverMessage.ok && serverMessage.detail && (
              <span>{serverMessage.status} - {serverMessage.detail}</span>
            )}
          </div>
        )}
      </div>

      {loading ? (
        <div className="connections__state">Загрузка…</div>
      ) : (
        <div className="connections__body">
          <ConnectionsList
            connections={connections}
            selectedName={selectedName}
            onSelect={handleSelect}
            search={search}
            testPassed={testPassed}
          />
          <ConnectionDetail connection={detail} loading={false} />
        </div>
      )}

      {showAddModal && (
        <AddConnectionModal
          onClose={() => setShowAddModal(false)}
          onSaved={handleSaved}
          pushMessage={pushMessage}
        />
      )}
    </div>
  );
}
