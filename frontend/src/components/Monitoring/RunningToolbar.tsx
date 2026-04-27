import './RunningToolbar.css';

const STATUS_BTNS = ['success', 'error', 'skipped', 'pending'] as const;
type StatusFilter = typeof STATUS_BTNS[number];

interface Props {
  onRefresh: () => void;
  refreshing: boolean;
  dateFrom: string;
  dateTo: string;
  onDateFromChange: (v: string) => void;
  onDateToChange: (v: string) => void;
  statusFilter: Set<StatusFilter>;
  onStatusToggle: (s: StatusFilter) => void;
  onStatusClear: () => void;
}

export default function RunningToolbar({
  onRefresh, refreshing, dateFrom, dateTo,
  onDateFromChange, onDateToChange, statusFilter, onStatusToggle, onStatusClear,
}: Props) {
  return (
    <div className="running-toolbar">
      <div className="running-toolbar__row">
        <div className="running-toolbar__group">
          <input
            className="running-toolbar__date-input"
            type="date"
            value={dateFrom}
            onChange={e => onDateFromChange(e.target.value)}
          />
          <input
            className="running-toolbar__date-input"
            type="date"
            value={dateTo}
            onChange={e => onDateToChange(e.target.value)}
          />
        </div>

        <button
          className={`running-toolbar__refresh${refreshing ? ' running-toolbar__refresh--spinning' : ''}`}
          title="Обновить"
          onClick={onRefresh}
          disabled={refreshing}
        >
          ↻
        </button>
      </div>

      <div className="running-toolbar__status-group">
        {STATUS_BTNS.map(s => (
          <button
            key={s}
            className={`running-toolbar__status-btn running-toolbar__status-btn--${s}${statusFilter.has(s) ? ' running-toolbar__status-btn--active' : ''}`}
            onClick={() => onStatusToggle(s)}
          >
            {s}
          </button>
        ))}
        {statusFilter.size > 0 && (
          <button className="running-toolbar__status-clear" onClick={onStatusClear} title="Сбросить фильтр">✕</button>
        )}
      </div>
    </div>
  );
}
