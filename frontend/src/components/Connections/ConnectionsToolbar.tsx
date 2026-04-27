import './ConnectionsToolbar.css';
import { PlugZap, Plus, Minus } from 'lucide-react';

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
        <button className="toolbar__btn toolbar__btn--primary" title="Добавить" onClick={onAdd}>
          <Plus size={15} strokeWidth={1.5} />
        </button>
        <button
          className="toolbar__btn toolbar__btn--primary"
          title={selectedName ? `Удалить` : 'Выберите подключение'}
          disabled={!selectedName || deleting}
          onClick={onDelete}
        >
          <Minus size={15} strokeWidth={1.9} />
        </button>
        <button
          className="toolbar__btn toolbar__btn--primary"
          title={selectedName ? `Тест` : 'Выберите подключение'}
          disabled={!selectedName || testing}
          onClick={onTest}
        >
          <PlugZap size={20} strokeWidth={1.2} />
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

      {/* {selectedName && (
        <span className="toolbar__selected-hint">Выбрано: {selectedName}</span>
      )} */}
    </div>
  );
}
