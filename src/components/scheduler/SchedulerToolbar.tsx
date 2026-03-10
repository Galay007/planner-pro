import { Button } from "@/components/ui/button";
import {
  Plus,
  Minus,
  Save,
  Settings,
} from "lucide-react";

interface SchedulerToolbarProps {
  onAdd: () => void;
  onRemove: () => void;
  onSave: () => void;
  onProperties: () => void;
  hasSelection: boolean;
  hasModified: boolean;
}

export function SchedulerToolbar({
  onAdd,
  onRemove,
  onSave,
  onProperties,
  hasSelection,
  hasModified,
}: SchedulerToolbarProps) {
  return (
    <div className="flex items-center gap-1 border border-border rounded-md bg-card p-1">
      <Button size="sm" variant="ghost" onClick={onAdd} title="Добавить задачу">
        <Plus className="h-4 w-4" />
      </Button>
      <Button
        size="sm"
        variant="ghost"
        onClick={onRemove}
        disabled={!hasSelection}
        title="Удалить задачу"
      >
        <Minus className="h-4 w-4" />
      </Button>
      <div className="w-px h-5 bg-border mx-1" />
      <Button
        size="sm"
        variant="ghost"
        onClick={onSave}
        disabled={!hasModified}
        title="Сохранить"
      >
        <Save className="h-4 w-4" />
      </Button>
      <Button
        size="sm"
        variant="ghost"
        onClick={onProperties}
        disabled={!hasSelection}
        title="Свойства"
      >
        <Settings className="h-4 w-4" />
      </Button>
    </div>
  );
}
