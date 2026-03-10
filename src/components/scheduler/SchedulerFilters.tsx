import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, FilterX } from "lucide-react";

interface SchedulerFiltersProps {
  search: string;
  onSearchChange: (value: string) => void;
  hasActiveFilters: boolean;
  onResetFilters: () => void;
}

export function SchedulerFilters({ search, onSearchChange, hasActiveFilters, onResetFilters }: SchedulerFiltersProps) {
  return (
    <div className="flex items-center gap-2">
      <div className="relative flex-1 min-w-[200px] max-w-[320px]">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
        <Input
          placeholder="Поиск..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-8 h-8 text-sm"
        />
      </div>
      <Button
        variant="ghost"
        size="sm"
        className="h-8 px-2 text-xs gap-1"
        disabled={!hasActiveFilters}
        onClick={onResetFilters}
      >
        <FilterX className="h-3.5 w-3.5" />
        Сбросить
      </Button>
    </div>
  );
}
