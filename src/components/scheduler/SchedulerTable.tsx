import { useState, useRef, useMemo } from "react";
import { Task, TaskControl } from "@/types/task";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EditableCell } from "./EditableCell";
import { BooleanCell } from "./BooleanCell";
import { DependencyCell } from "./DependencyCell";
import { ArrowUpDown, Play, Square } from "lucide-react";
import { LogsDialog } from "./LogsDialog";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ColumnFilterPopover } from "./ColumnFilterPopover";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

type ColumnFilters = Record<string, Set<string>>;

interface SchedulerTableProps {
  tasks: Task[];
  allTasks: Task[];
  allTaskIds: number[];
  selectedId: number | null;
  onSelect: (id: number | null) => void;
  onUpdate: (id: number, updates: Partial<Task>) => void;
  onControlUpdate: (id: number, control: TaskControl, status: Task["status"]) => void;
  columnFilters: ColumnFilters;
  onColumnFiltersChange: (filters: ColumnFilters) => void;
}

type SortKey = "id" | "name" | "group" | "employee" | "control" | "dependency" | "status" | "next_launch" | "notifications" | "logs" | "comment" | "properties";
type SortDir = "asc" | "desc" | "none";

const statusLabels: Record<Task["status"], string> = {
  idle: "Остановлен",
  running: "Активный",
  success: "Успешно",
  error: "Ошибка",
};

const statusColors: Record<Task["status"], string> = {
  idle: "text-muted-foreground",
  running: "text-primary",
  success: "text-primary",
  error: "text-destructive",
};

const statusFilterOptions = [
  { value: "idle", label: "Остановлен" },
  { value: "running", label: "Активный" },
  { value: "success", label: "Успешно" },
  { value: "error", label: "Ошибка" },
];

const controlFilterOptions = [
  { value: "play", label: "Запущен" },
  { value: "stop", label: "Остановлен" },
];

const propertiesFilterOptions = [
  { value: "set", label: "Заданы" },
  { value: "unset", label: "Не заданы" },
];

const notificationsFilterOptions = [
  { value: "true", label: "Включены" },
  { value: "false", label: "Выключены" },
];

export function SchedulerTable({
  tasks,
  allTasks,
  allTaskIds,
  selectedId,
  onSelect,
  onUpdate,
  onControlUpdate,
  columnFilters,
  onColumnFiltersChange,
}: SchedulerTableProps) {
  const [sortKey, setSortKey] = useState<SortKey | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>("none");
  const [logsTaskId, setLogsTaskId] = useState<number | null>(null);
  const [pendingControl, setPendingControl] = useState<{ taskId: number; ctrl: TaskControl } | null>(null);
  const [unsavedPlayWarning, setUnsavedPlayWarning] = useState<number | null>(null);
  const [emptyFieldsWarning, setEmptyFieldsWarning] = useState<{ taskId: number; fields: string[] } | null>(null);
  const [unsetPropertiesWarning, setUnsetPropertiesWarning] = useState<number | null>(null);
  const sortedOrderRef = useRef<number[]>([]);

  const logsTask = tasks.find((t) => t.id === logsTaskId);

  // Compute dynamic filter options from all tasks (not filtered)
  const getNextLaunchLabel = (task: Task) => {
    if (task.properties === "unset") return "—";
    if (task.dependency !== null) return `После ID ${task.dependency}`;
    return "08.03.26 в 13:00";
  };

  const dynamicOptions = useMemo(() => {
    const uniqueNames = [...new Set(allTasks.map(t => t.name).filter(Boolean))];
    const uniqueGroups = [...new Set(allTasks.map(t => t.group).filter(Boolean))];
    const uniqueEmployees = [...new Set(allTasks.map(t => t.employee).filter(Boolean))];
    const uniqueComments = [...new Set(allTasks.map(t => t.comment).filter(Boolean))];
    const uniqueIds = [...new Set(allTasks.map(t => String(t.id)))];
    const uniqueDeps = [...new Set(allTasks.map(t => String(t.dependency ?? "")).filter(Boolean))];
    const uniqueNextLaunch = [...new Set(allTasks.map(t => getNextLaunchLabel(t)))];
    return {
      id: uniqueIds.map(v => ({ value: v, label: v })),
      name: uniqueNames.map(v => ({ value: v, label: v })),
      group: uniqueGroups.map(v => ({ value: v, label: v })),
      employee: uniqueEmployees.map(v => ({ value: v, label: v })),
      comment: uniqueComments.map(v => ({ value: v, label: v })),
      dependency: uniqueDeps.map(v => ({ value: v, label: `ID ${v}` })),
      next_launch: uniqueNextLaunch.map(v => ({ value: v, label: v })),
    };
  }, [allTasks]);

  const setColumnFilter = (key: string, selected: Set<string>) => {
    const next = { ...columnFilters };
    if (selected.size === 0) {
      delete next[key];
    } else {
      next[key] = selected;
    }
    onColumnFiltersChange(next);
  };

  const computeSortedOrder = (taskList: Task[], key: SortKey, dir: "asc" | "desc") => {
    return [...taskList].sort((a, b) => {
      const av = a[key];
      const bv = b[key];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      const cmp = typeof av === "string" ? av.localeCompare(bv as string) : Number(av) - Number(bv);
      return dir === "asc" ? cmp : -cmp;
    }).map(t => t.id);
  };

  const toggleSort = (key: SortKey) => {
    let newDir: SortDir;
    if (sortKey === key) {
      newDir = sortDir === "asc" ? "desc" : sortDir === "desc" ? "none" : "asc";
    } else {
      newDir = "asc";
    }
    if (newDir === "none") {
      setSortKey(null);
      setSortDir("none");
      sortedOrderRef.current = [];
    } else {
      setSortKey(key);
      setSortDir(newDir);
      sortedOrderRef.current = computeSortedOrder(tasks, key, newDir);
    }
    onSelect(null);
  };

  const frozenOrder = sortedOrderRef.current;
  const frozenSet = new Set(frozenOrder);
  const newTasks = tasks.filter((t) => !frozenSet.has(t.id));
  const taskMap = new Map(tasks.map(t => [t.id, t]));
  const sorted = [
    ...frozenOrder.filter(id => taskMap.has(id)).map(id => taskMap.get(id)!),
    ...newTasks,
  ];

  const FilterIcon = ({ field, options }: { field: string; options: { value: string; label: string }[] }) => {
    if (options.length === 0) return (
      <ColumnFilterPopover
        options={[]}
        selected={columnFilters[field] ?? new Set()}
        onChange={(sel) => setColumnFilter(field, sel)}
      />
    );
    return (
      <ColumnFilterPopover
        options={options}
        selected={columnFilters[field] ?? new Set()}
        onChange={(sel) => setColumnFilter(field, sel)}
      />
    );
  };

  const SortHeader = ({ label, field, centered, filterOptions }: { label: React.ReactNode; field: SortKey; centered?: boolean; filterOptions?: { value: string; label: string }[] }) => (
    <div className={cn("flex items-center gap-1 select-none", centered && "justify-center")}>
      <div
        className="flex items-center gap-1 cursor-pointer hover:text-foreground transition-colors"
        onClick={() => toggleSort(field)}
      >
        {label}
        <ArrowUpDown className={cn("h-3 w-3", sortKey === field && sortDir !== "none" ? "text-primary" : "text-muted-foreground/50")} />
      </div>
      {filterOptions && <FilterIcon field={field} options={filterOptions} />}
    </div>
  );

  return (
    <div className="border border-border rounded-md overflow-auto flex-1 bg-card [&_th:not(:last-child)]:border-r [&_th:not(:last-child)]:border-border/40 [&_td:not(:last-child)]:border-r [&_td:not(:last-child)]:border-border/30">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent border-b border-border">
            <TableHead className="w-5 px-1 text-center"><SortHeader label="ID" field="id" filterOptions={dynamicOptions.id} /></TableHead>
            <TableHead className="w-15 px-1"><SortHeader label="Управление" field="control" filterOptions={controlFilterOptions} /></TableHead>
            <TableHead className="min-w-[180px]"><SortHeader label="Задача" field="name" centered filterOptions={dynamicOptions.name} /></TableHead>
            <TableHead className="min-w-[140px]"><SortHeader label="Группа" field="group" centered filterOptions={dynamicOptions.group} /></TableHead>
            <TableHead className="min-w-[140px]"><SortHeader label="Автор" field="employee" centered filterOptions={dynamicOptions.employee} /></TableHead>
            <TableHead className="w-28"><SortHeader label="Статус" field="status" filterOptions={statusFilterOptions} /></TableHead>
            <TableHead className="whitespace-nowrap"><SortHeader label="След. запуск" field="next_launch" filterOptions={dynamicOptions.next_launch} /></TableHead>
            <TableHead className="w-10 px-1 text-center"><SortHeader label={<div className="flex flex-wrap justify-center"><span className="whitespace-nowrap">Связь с</span><span>ID</span></div>} field="dependency" centered filterOptions={dynamicOptions.dependency} /></TableHead>
            <TableHead className="w-20 text-center"><SortHeader label="Уведомл." field="notifications" centered filterOptions={notificationsFilterOptions} /></TableHead>
            <TableHead className="w-20 text-center"><SortHeader label="Логи" field="logs" centered /></TableHead>
            <TableHead className="w-24 text-center"><SortHeader label="Свойства" field="properties" centered filterOptions={propertiesFilterOptions} /></TableHead>
            <TableHead className="min-w-[140px]"><SortHeader label="Комментарий" field="comment" centered filterOptions={dynamicOptions.comment} /></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.length === 0 && (
            <TableRow>
              <TableCell colSpan={12} className="text-center text-muted-foreground py-12">
                Нажмите «+» чтобы добавить задачу
              </TableCell>
            </TableRow>
          )}
          {sorted.map((task) => (
            <TableRow
              key={task.id}
              onClick={() => onSelect(task.id)}
              className={cn(
                "cursor-pointer transition-colors !border-b !border-border",
                selectedId === task.id
                  ? "bg-accent/40 shadow-[inset_2px_0_0_0_hsl(var(--primary))]"
                  : "hover:bg-muted/30"
              )}
            >
              <TableCell className="font-mono text-muted-foreground text-sm text-center px-1 !cursor-default">
                {task.id}
              </TableCell>
              <TableCell>
                <div className="flex items-center justify-center">
                  {(["play", "stop"] as TaskControl[]).map((ctrl) => {
                    const isActive = task.control === ctrl;
                    const Icon = ctrl === "play" ? Play : Square;
                    return (
                      <Button
                        key={ctrl}
                        variant="ghost"
                        size="icon"
                        className={cn(
                          "h-7 w-7",
                          isActive
                            ? ctrl === "play"
                              ? "text-primary bg-primary/15"
                              : "text-destructive bg-destructive/15"
                            : "text-muted-foreground hover:text-foreground"
                        )}
                        onClick={(e) => {
                          e.stopPropagation();
                          if (task.control !== ctrl) {
                            if (ctrl === "play") {
                              const modifiedTask = tasks.find((t) => t.modified);
                              if (modifiedTask) {
                                setUnsavedPlayWarning(modifiedTask.id);
                                return;
                              }
                              if (task.properties === "unset") {
                                setUnsetPropertiesWarning(task.id);
                                return;
                              }
                              const missingFields: string[] = [];
                              if (!task.name.trim()) missingFields.push("Задача");
                              if (!task.employee.trim()) missingFields.push("Автор");
                              if (missingFields.length > 0) {
                                setEmptyFieldsWarning({ taskId: task.id, fields: missingFields });
                                return;
                              }
                            }
                            onSelect(task.id);
                            setPendingControl({ taskId: task.id, ctrl });
                          }
                        }}
                      >
                        <Icon className="h-3.5 w-3.5" />
                      </Button>
                    );
                  })}
                </div>
              </TableCell>
              <TableCell>
                <EditableCell
                  value={task.name}
                  onChange={(v) => onUpdate(task.id, { name: v })}
                  disabled={task.control === "play"}
                />
              </TableCell>
              <TableCell>
                <EditableCell
                  value={task.group}
                  placeholder="—"
                  onChange={(v) => onUpdate(task.id, { group: v })}
                  disabled={task.control === "play"}
                />
              </TableCell>
              <TableCell>
                <EditableCell
                  value={task.employee}
                  placeholder=""
                  onChange={(v) => onUpdate(task.id, { employee: v })}
                  disabled={task.control === "play"}
                />
              </TableCell>
              <TableCell className="cursor-default">
                <span className={cn("text-sm font-medium", statusColors[task.status])}>
                  {statusLabels[task.status]}
                </span>
              </TableCell>
              <TableCell className="text-center cursor-default">
                <span className="text-sm font-medium text-muted-foreground">
                  {task.properties === "unset"
                    ? "—"
                    : task.dependency === null
                      ? "08.03.26 в 13:00"
                      : `После ID ${task.dependency}`}
                </span>
              </TableCell>
              <TableCell>
                <div className="flex items-center justify-center">
                  <DependencyCell
                    value={task.dependency}
                    currentId={task.id}
                    allIds={allTaskIds}
                    onChange={(v) => onUpdate(task.id, { dependency: v })}
                    disabled={task.control === "play"}
                  />
                </div>
              </TableCell>
              <TableCell className="text-center px-0">
                <BooleanCell
                  value={task.notifications}
                  disabled={task.control === "play"}
                  onChange={(v) => {
                    onSelect(task.id);
                    onUpdate(task.id, { notifications: v });
                  }}
                />
              </TableCell>
              <TableCell>
                <div className="flex justify-center">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2 text-sm text-muted-foreground hover:text-foreground"
                    onClick={(e) => {setLogsTaskId(task.id);
                    }}
                  >
                    Открыть
                  </Button>
                </div>
              </TableCell>
              <TableCell className="text-center cursor-default">
                <span className={cn("text-sm font-medium", task.properties === "set" ? "text-primary" : "text-muted-foreground")}>
                  {task.properties === "set" ? "Заданы" : "Не заданы"}
                </span>
              </TableCell>
              <TableCell>
                <EditableCell
                  value={task.comment}
                  placeholder=""
                  onChange={(v) => onUpdate(task.id, { comment: v })}
                  disabled={task.control === "play"}
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <LogsDialog
        open={logsTaskId !== null}
        onOpenChange={(open) => !open && setLogsTaskId(null)}
        taskId={logsTask?.id ?? 0}
        logs={logsTask?.logs ?? ""}
      />
      <AlertDialog open={pendingControl !== null} onOpenChange={(open) => !open && setPendingControl(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Подтверждение</AlertDialogTitle>
            <AlertDialogDescription>
              {pendingControl?.ctrl === "play"
                ? <>Задача ID {pendingControl?.taskId} будет <strong className="font-bold">ЗАПУЩЕНА</strong>, продолжить?</>
                : <>Задача ID {pendingControl?.taskId} будет <strong className="font-bold">ОСТАНОВЛЕНА</strong>, продолжить?</>}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (pendingControl) {
                  onControlUpdate(
                    pendingControl.taskId,
                    pendingControl.ctrl,
                    pendingControl.ctrl === "play" ? "running" : "idle"
                  );
                }
                setPendingControl(null);
              }}
            >
              Продолжить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      <AlertDialog open={unsavedPlayWarning !== null} onOpenChange={(open) => !open && setUnsavedPlayWarning(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Внимание</AlertDialogTitle>
            <AlertDialogDescription>
              Сохраните изменения задачи ID {unsavedPlayWarning} перед запуском.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogAction onClick={() => setUnsavedPlayWarning(null)}>
              Ок
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      <AlertDialog open={emptyFieldsWarning !== null} onOpenChange={(open) => !open && setEmptyFieldsWarning(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Внимание</AlertDialogTitle>
            <AlertDialogDescription>
              Заполните поля {emptyFieldsWarning?.fields.join(" и ")} для задачи ID {emptyFieldsWarning?.taskId} перед запуском.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogAction onClick={() => setEmptyFieldsWarning(null)}>
              Ок
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      <AlertDialog open={unsetPropertiesWarning !== null} onOpenChange={(open) => !open && setUnsetPropertiesWarning(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Внимание</AlertDialogTitle>
            <AlertDialogDescription>
              Невозможно запустить задачу ID {unsetPropertiesWarning} пока не заданы ее свойства.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogAction onClick={() => setUnsetPropertiesWarning(null)}>
              Ок
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
