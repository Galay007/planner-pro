import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface BooleanPopoverProps {
  value: boolean;
  onChange: (value: boolean) => void;
  labelTrue?: string;
  labelFalse?: string;
}

export function BooleanPopover({
  value,
  onChange,
  labelTrue = "Да",
  labelFalse = "Нет",
}: BooleanPopoverProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          onClick={(e) => e.stopPropagation()}
          className={cn(
            "text-xs font-medium px-2 py-0.5 rounded border border-border hover:border-primary/50 transition-colors",
            value ? "text-primary" : "text-muted-foreground"
          )}
        >
          {value ? labelTrue : labelFalse}
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-28 p-1" align="start">
        <Button
          variant={value ? "default" : "ghost"}
          size="sm"
          className="w-full justify-start text-xs"
          onClick={() => onChange(true)}
        >
          {labelTrue}
        </Button>
        <Button
          variant={!value ? "default" : "ghost"}
          size="sm"
          className="w-full justify-start text-xs"
          onClick={() => onChange(false)}
        >
          {labelFalse}
        </Button>
      </PopoverContent>
    </Popover>
  );
}
