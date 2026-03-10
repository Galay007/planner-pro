import { toast } from "sonner";
import { Checkbox } from "@/components/ui/checkbox";

interface BooleanCellProps {
  value: boolean;
  onChange: (value: boolean) => void;
  disabled?: boolean;
}

export function BooleanCell({ value, onChange, disabled }: BooleanCellProps) {
  return (
    <div
      className="flex justify-center min-h-[24px] items-center"
      onClick={(e) => {
        e.stopPropagation();
        if (disabled) {
          toast.warning("Изменения нельзя внести, пока задача не остановлена.");
          return;
        }
        onChange(!value);
      }}
    >
      <Checkbox checked={value} disabled className="pointer-events-none" />
    </div>
  );
}
