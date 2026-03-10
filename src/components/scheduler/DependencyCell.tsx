import { useState, useRef, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

interface DependencyCellProps {
  value: number | null;
  currentId: number;
  allIds: number[];
  onChange: (value: number | null) => void;
  disabled?: boolean;
}

export function DependencyCell({ value, currentId, allIds, onChange, disabled }: DependencyCellProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value?.toString() ?? "");
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing) {
      inputRef.current?.focus();
      inputRef.current?.select();
    }
  }, [editing]);

  useEffect(() => {
    setDraft(value?.toString() ?? "");
  }, [value]);

  const validate = (val: string): boolean => {
    if (val.trim() === "") {
      setError("");
      return true;
    }
    const num = parseInt(val, 10);
    if (isNaN(num) || num.toString() !== val.trim()) {
      setError("Целое число");
      return false;
    }
    if (num === currentId) {
      setError("Не текущая");
      return false;
    }
    if (!allIds.includes(num)) {
      setError("Не найдена");
      return false;
    }
    setError("");
    return true;
  };

  const commit = () => {
    if (validate(draft)) {
      onChange(draft.trim() === "" ? null : parseInt(draft, 10));
      setEditing(false);
      setError("");
    }
  };

  if (!editing) {
    return (
      <div
        className="text-xs font-mono text-muted-foreground min-h-[24px] px-1 py-0.5 rounded cursor-text hover:bg-muted/40 transition-colors"
        onDoubleClick={(e) => {
          e.stopPropagation();
          if (disabled) {
            toast.warning("Изменения нельзя внести, пока задача не остановлена.");
            return;
          }
          setEditing(true);
        }}
      >
        {value ?? <span className="text-muted-foreground/50 text-xs">—</span>}
      </div>
    );
  }

  return (
    <div onClick={(e) => e.stopPropagation()}>
      <Input
        ref={inputRef}
        value={draft}
        onChange={(e) => {
          setDraft(e.target.value);
          validate(e.target.value);
        }}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === "Enter") commit();
          if (e.key === "Escape") {
            setDraft(value?.toString() ?? "");
            setError("");
            setEditing(false);
          }
        }}
        className={`h-7 text-sm font-mono order-0 ${error ? "ring-2 ring-destructive" : ""}`}
      />
      {error && <p className="text-destructive text-[10px] mt-0.5">{error}</p>}
    </div>
  );
}
