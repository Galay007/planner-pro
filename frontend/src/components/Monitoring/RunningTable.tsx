import { useState } from 'react';
import type { TaskRunningOut } from '../../types';
import './RunningTable.css';

type SortKey = keyof TaskRunningOut;
type SortDir = 'asc' | 'desc';

interface Props {
  rows: TaskRunningOut[];
}

const COLUMNS: { key: SortKey; label: string }[] = [
  { key: 'task_id',       label: 'ID' },
  { key: 'task_name',     label: 'Имя задачи' },
  { key: 'parent_id',     label: 'Родитель' },
  { key: 'trigger_mode',  label: 'Режим' },
  { key: 'schedule_dt',   label: 'Расписание' },
  { key: 'worker_id',     label: 'Воркер' },
  { key: 'started_str',    label: 'Запуск' },
  { key: 'finished_str',   label: 'Завершено' },
  { key: 'duration',      label: 'Длит.' },
  { key: 'attempt_count', label: 'Попыток' },
  { key: 'next_retry_at', label: 'След. попытка' },
  { key: 'status',        label: 'Статус' },
];

function fmt(val: string | number | null | undefined): string {
  if (val === null || val === undefined) return '';
  if (typeof val === 'string' && val.includes('T')) return val.replace('T', ' ').slice(0, 16);
  return String(val);
}

export default function RunningTable({ rows }: Props) {
  const [sortKey, setSortKey] = useState<SortKey | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('asc'); }
  }

  const sorted = sortKey === null ? [...rows] : [...rows].sort((a, b) => {
    const av = a[sortKey] ?? '';
    const bv = b[sortKey] ?? '';
    if (av < bv) return sortDir === 'asc' ? -1 : 1;
    if (av > bv) return sortDir === 'asc' ? 1 : -1;
    return 0;
  });

  return (
    <div className="running-table__wrap">
      <table className="running-table">
        <thead>
          <tr>
            {COLUMNS.map(col => (
              <th
                key={col.key}
                className="running-table__th"
                onClick={() => toggleSort(col.key)}
              >
                {col.label}
                {sortKey === col.key
                  ? <span className="running-table__sort">{sortDir === 'asc' ? ' ↑' : ' ↓'}</span>
                  : <span className="running-table__sort running-table__sort--inactive"> ↕</span>}

              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.length === 0 ? (
            <tr>
              <td className="running-table__empty" colSpan={COLUMNS.length}>Нет данных</td>
            </tr>
          ) : sorted.map((row, i) => (
            <tr key={i} className="running-table__tr">
              {COLUMNS.map(col => (
                <td key={col.key} className={`running-table__td${col.key === 'status' ? ` running-table__td--status running-table__td--${row.status ?? ''}` : col.key === 'task_id' ? ' running-table__td--id' : col.key !== 'task_name' ? ' running-table__td--center' : ''}`}>
                  {fmt(row[col.key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
