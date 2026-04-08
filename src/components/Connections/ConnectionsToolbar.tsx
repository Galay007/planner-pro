import './ConnectionsToolbar.css';

interface Props {
  onAdd: () => void;
  onDelete: () => void;
  onTest: () => void;
  onRefresh: () => void;
  selectedName: string | null;
  deleting: boolean;
  testing: boolean;
  refreshing: boolean;
}

export default function ConnectionsToolbar({
  onAdd, onDelete, onTest, onRefresh,
  selectedName, deleting, testing, refreshing,
}: Props) {
  return (
    <div className="toolbar">
      <div className="toolbar__group">
        <button className="toolbar__btn toolbar__btn--primary" title="Добавить подключение" onClick={onAdd}>
          +
        </button>
        <button
          className="toolbar__btn toolbar__btn--danger"
          title={selectedName ? `Удалить ${selectedName}` : 'Выберите подключение'}
          disabled={!selectedName || deleting}
          onClick={onDelete}
        >
          −
        </button>
        <button
          className="toolbar__btn toolbar__btn--test"
          title={selectedName ? `Тест ${selectedName}` : 'Выберите подключение'}
          disabled={!selectedName || testing}
          onClick={onTest}
        >
          ⚡
        </button>
      </div>

      <div className="toolbar__divider" />

      <button
        className={`toolbar__btn toolbar__btn--refresh${refreshing ? ' toolbar__btn--spinning' : ''}`}
        title="Обновить список"
        onClick={onRefresh}
        disabled={refreshing}
      >
        ↻
      </button>

      {selectedName && (
        <span className="toolbar__selected-hint">Выбрано: {selectedName}</span>
      )}
    </div>
  );
}
