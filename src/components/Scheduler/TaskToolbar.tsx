import './TaskToolbar.css';

interface Props {
  onAdd: () => void;
  adding: boolean;
  onRefresh: () => void;
  refreshing: boolean;
  selectedId: number | null;
  onDelete: () => void;
  deleting: boolean;
}

export default function TaskToolbar({ onAdd, adding, onRefresh, refreshing, selectedId, onDelete, deleting }: Props) {
  return (
    <div className="toolbar">
      <div className="toolbar__group">
        <button
          className="toolbar__btn toolbar__btn--primary"
          title="Добавить задачу"
          disabled={adding}
          onClick={onAdd}
        >
          {adding ? '…' : '+'}
        </button>
        <button
          className="toolbar__btn toolbar__btn--primary"
          title={selectedId ? `Удалить задачу #${selectedId}` : 'Выберите задачу для удаления'}
          disabled={selectedId === null || deleting}
          onClick={onDelete}
        >
          {deleting ? '…' : '−'}
        </button>
        <button className="toolbar__btn" title="Копировать задачу">
          ⧉
        </button>
        <button className="toolbar__btn" title="Настройки">
          ⚙
        </button>
      </div>

      <div className="toolbar__divider" />

      <button
        className={`toolbar__btn toolbar__btn--refresh${refreshing ? ' toolbar__btn--spinning' : ''}`}
        title="Обновить список задач"
        onClick={onRefresh}
        disabled={refreshing}
      >
        ↻
      </button>

      {selectedId !== null && (
        <span className="toolbar__selected-hint">
          Выбрана задача #{selectedId}
        </span>
      )}
    </div>
  );
}
