import { useState, useRef, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

interface EditableCellProps {
  value: string;
  placeholder?: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function EditableCell({ value, placeholder, onChange, disabled }: EditableCellProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing) {
      inputRef.current?.focus();
      inputRef.current?.select();
    }
  }, [editing]);

  useEffect(() => {
    setDraft(value);
  }, [value]);

  if (!editing) {
    return (
      <div
        className="text-sm text-muted-foreground min-h-[28px] leading-7 px-1 py-0 rounded cursor-text hover:bg-muted/40 transition-colors"
        onDoubleClick={(e) => {
          e.stopPropagation();
          if (disabled) {
            toast.warning("Изменения нельзя внести, пока задача не остановлена.");
            return;
          }
          setEditing(true);
        }}
      >
        {value || <span className="text-muted-foreground/50 text-sm">{placeholder}</span>}
      </div>
    );
  }

  return (
    <Input
      ref={inputRef}
      value={draft}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={() => {
        if (draft !== value) {
          onChange(draft);
        }
        setEditing(false);
      }}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          onChange(draft);
          setEditing(false);
        }
        if (e.key === "Escape") {
          setDraft(value);
          setEditing(false);
        }
      }}
      onClick={(e) => e.stopPropagation()}
      className="h-7 !text-sm bg-muted border-0 px-1 py-0"
    />
  );
}
