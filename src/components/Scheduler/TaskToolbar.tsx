import './TaskToolbar.css';
import { Plus, Minus } from 'lucide-react';

interface Props {
  onAdd: () => void;
  adding: boolean;
  editing: boolean;
  onRefresh: () => void;
  refreshing: boolean;
  selectedId: number | null;
  onDelete: () => void;
  deleting: boolean;
}

export default function TaskToolbar({ onAdd, adding, editing, onRefresh, refreshing, selectedId, onDelete, deleting }: Props) {
  return (
    <div className="toolbar">
      <div className="toolbar__group">
        <button
          className="toolbar__btn toolbar__btn--primary"
          title="Добавить задачу"
          disabled={adding || editing}
          onClick={onAdd}
        >
          <Plus size={15} strokeWidth={1.5} />
        </button>
        <button
          className="toolbar__btn toolbar__btn--primary"
          title={selectedId ? `Удалить задачу #${selectedId}` : 'Выберите задачу для удаления'}
          disabled={selectedId === null || deleting || editing}
          onClick={onDelete}
        >
          <Minus size={15} strokeWidth={1.5} />
        </button>
      </div>

      <div className="toolbar__divider" />

      <button
        className={`toolbar__btn toolbar__btn--refresh${refreshing ? ' toolbar__btn--spinning' : ''}`}
        title="Обновить"
        onClick={onRefresh}
        disabled={refreshing}
      >
        ↻
      </button>

      {/* {selectedId !== null && (
        <span className="toolbar__selected-hint">
          Выбрана задача #{selectedId}
        </span>
      )} */}
    </div>
  );
}
