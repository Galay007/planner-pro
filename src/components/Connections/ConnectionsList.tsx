import { useState } from 'react';
import type { ConnType } from '../../types';
import './ConnectionsList.css';

interface ConnItem {
  name: string;
  conn_type: ConnType;
}

interface Props {
  connections: ConnItem[];
  selectedName: string | null;
  onSelect: (name: string) => void;
  search: string;
  testPassedName: string | null;
}

const COLS = (
  <colgroup>
    <col style={{ width: '60%' }} />
    <col style={{ width: '50%' }} />
  </colgroup>
);

export default function ConnectionsList({ connections, selectedName, onSelect, search, testPassedName }: Props) {
  const [sortCol, setSortCol] = useState<'name' | 'conn_type' | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  function toggleSort(col: 'name' | 'conn_type') {
    if (sortCol === col) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortCol(col); setSortDir('asc'); }
  }

  const filtered = connections
    .filter((c) => {
      const q = search.toLowerCase();
      return c.name.toLowerCase().includes(q) || c.conn_type.toLowerCase().includes(q);
    })
    .sort((a, b) => {
      if (!sortCol) return 0;
      const cmp = a[sortCol].localeCompare(b[sortCol]);
      return sortDir === 'asc' ? cmp : -cmp;
    });

    
  function sortIcon(col: 'name' | 'conn_type') {
    if (sortCol !== col) return <span className="conn-list__sort-icon">⇅</span>;
    return <span className="conn-list__sort-icon conn-list__sort-icon--active">{sortDir === 'asc' ? '↑' : '↓'}</span>;
  }

  return (
    <div className="conn-list">
      <table className="conn-list__table">
        {COLS}
        <thead>
          <tr>
            <th className="conn-list__th" onClick={() => toggleSort('name')}>
              Имя {sortIcon('name')}
            </th>
            <th className="conn-list__th" onClick={() => toggleSort('conn_type')}>
              Тип {sortIcon('conn_type')}
            </th>
          </tr>
        </thead>
      </table>

      {filtered.length === 0 ? (
        <div className="conn-list__empty">Нет подключений</div>
      ) : (
        <div className="conn-list__scroll">
          <table className="conn-list__table">
            {COLS}
            <tbody>
              {filtered.map((c) => (
                <tr
                  key={c.name}
                  className={`conn-list__tr${selectedName === c.name ? ' conn-list__tr--active' : ''}`}
                  onClick={() => onSelect(c.name)}
                >
                  <td className="conn-list__td">
                    {c.name}
                    {testPassedName === c.name && <span className="conn-list__dot" />}
                  </td>
                  <td className="conn-list__td">{c.conn_type}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
