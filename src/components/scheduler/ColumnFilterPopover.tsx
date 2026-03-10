import { useState } from "react";
import { Filter } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ColumnFilterPopoverProps {
  options: { value: string; label: string }[];
  selected: Set<string>;
  onChange: (selected: Set<string>) => void;
}

export function ColumnFilterPopover({ options, selected, onChange }: ColumnFilterPopoverProps) {
  const [open, setOpen] = useState(false);
  const isActive = selected.size > 0 && selected.size < options.length;

  const toggleValue = (value: string) => {
    const next = new Set(selected);
    if (next.has(value)) {
      next.delete(value);
    } else {
      next.add(value);
    }
    onChange(next);
  };

  const selectAll = () => onChange(new Set());
  const isAllSelected = selected.size === 0;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          className={cn(
            "inline-flex items-center justify-center h-4 w-4 rounded-sm transition-colors shrink-0",
            isActive
              ? "text-primary"
              : "text-muted-foreground/40 hover:text-muted-foreground"
          )}
          onClick={(e) => e.stopPropagation()}
        >
          <Filter className="h-3 w-3" fill={isActive ? "currentColor" : "none"} />
        </button>
      </PopoverTrigger>
      <PopoverContent
        className="w-auto min-w-[140px] p-2"
        align="start"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex flex-col gap-1">
          <label className="flex items-center gap-2 px-1 py-0.5 text-xs cursor-pointer hover:bg-muted/50 rounded">
            <Checkbox
              checked={isAllSelected}
              onCheckedChange={() => selectAll()}
              className="h-3.5 w-3.5"
            />
            <span className="text-muted-foreground">Все</span>
          </label>
          <div className="h-px bg-border my-0.5" />
          {options.map((opt) => (
            <label
              key={opt.value}
              className="flex items-center gap-2 px-1 py-0.5 text-xs cursor-pointer hover:bg-muted/50 rounded"
            >
              <Checkbox
                checked={selected.size === 0 || selected.has(opt.value)}
                onCheckedChange={() => toggleValue(opt.value)}
                className="h-3.5 w-3.5"
              />
              <span>{opt.label}</span>
            </label>
          ))}
          {isActive && (
            <>
              <div className="h-px bg-border my-0.5" />
              <Button
                variant="ghost"
                size="sm"
                className="h-6 text-xs justify-start px-1"
                onClick={() => selectAll()}
              >
                Сбросить
              </Button>
            </>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
