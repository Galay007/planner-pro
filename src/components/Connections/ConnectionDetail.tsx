import type { ConnectionOut } from '../../types';
import './ConnectionDetail.css';

interface Props {
  connection: ConnectionOut | null;
  loading: boolean;
}

const LABELS: Record<keyof ConnectionOut, string> = {
  name: 'Имя',
  conn_type: 'Тип',
  host: 'Хост',
  port: 'Порт',
  db_name: 'База данных',
  login: 'Логин',
  db_path: 'Путь к файлу',
};

const SQLITE_ONLY: (keyof ConnectionOut)[] = ['db_path'];
const NON_SQLITE: (keyof ConnectionOut)[] = ['host', 'port', 'db_name', 'login'];

export default function ConnectionDetail({ connection, loading }: Props) {
  if (loading) {
    return <div className="conn-detail conn-detail--empty">Загрузка…</div>;
  }

  if (!connection) {
    return (
      <div className="conn-detail conn-detail--empty">
        Выберите подключение из списка
      </div>
    );
  }

  const isSqlite = connection.conn_type === 'sqlite';

  const fields: (keyof ConnectionOut)[] = [
    'name',
    'conn_type',
    ...(isSqlite ? SQLITE_ONLY : NON_SQLITE),
  ];

  return (
    <div className="conn-detail">
      <div className="conn-detail__header">{connection.name}</div>
      <table className="conn-detail__table">
        <tbody>
          {fields.map((key) => (
            <tr key={key} className="conn-detail__row">
              <td className="conn-detail__label">{LABELS[key]}</td>
              <td className="conn-detail__value">{connection[key] || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
