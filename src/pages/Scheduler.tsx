import { useState, useCallback, useRef, useMemo } from "react";
import { Task } from "@/types/task";
import { SchedulerToolbar } from "@/components/scheduler/SchedulerToolbar";
import { SchedulerTable } from "@/components/scheduler/SchedulerTable";
import { SchedulerFilters } from "@/components/scheduler/SchedulerFilters";
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

export type ColumnFilters = Record<string, Set<string>>;

const Scheduler = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [nextId, setNextId] = useState(1);
  const [saveConfirmId, setSaveConfirmId] = useState<number | null>(null);
  const [pendingSelectId, setPendingSelectId] = useState<number | null>(null);
  const [unsavedPromptId, setUnsavedPromptId] = useState<number | null>(null);
  const taskSnapshotsRef = useRef<Map<number, Task>>(new Map());
  const [search, setSearch] = useState("");
  const [columnFilters, setColumnFilters] = useState<ColumnFilters>({});

  const getNextLaunchLabel = (t: Task) => {
    if (t.properties === "unset") return "—";
    if (t.dependency !== null) return `После ID ${t.dependency}`;
    return "08.03.26 в 13:00";
  };

  const filteredTasks = useMemo(() => {
    return tasks.filter((t) => {
      if (search) {
        const q = search.toLowerCase();
        const match =
          t.name.toLowerCase().includes(q) ||
          t.group.toLowerCase().includes(q) ||
          t.employee.toLowerCase().includes(q) ||
          t.comment.toLowerCase().includes(q) ||
          String(t.id).includes(q);
        if (!match) return false;
      }
      for (const [key, selected] of Object.entries(columnFilters)) {
        if (selected.size === 0) continue;
        if (key === "next_launch") {
          const value = getNextLaunchLabel(t);
          if (!selected.has(value)) return false;
        } else {
          const value = String(t[key as keyof Task] ?? "");
          if (!selected.has(value)) return false;
        }
      }
      return true;
    });
  }, [tasks, search, columnFilters]);

  const hasActiveFilters = search.length > 0 || Object.keys(columnFilters).length > 0;

  const resetAllFilters = useCallback(() => {
    setSearch("");
    setColumnFilters({});
  }, []);

  const addTask = useCallback(() => {
    const newTask: Task = {
      id: nextId,
      name: "",
      group: "",
      employee: "",
      control: "stop",
      dependency: null,
      status: "idle",
      notifications: false,
      logs: "",
      comment: "",
      properties: "unset",
      modified: false,
    };
    setTasks((prev) => [...prev, newTask]);
    setNextId((n) => n + 1);
  }, [nextId]);

  const removeTask = useCallback(() => {
    if (selectedId === null) return;
    setTasks((prev) => prev.filter((t) => t.id !== selectedId));
    setSelectedId(null);
  }, [selectedId]);

  const updateTask = useCallback((id: number, updates: Partial<Task>) => {
    setTasks((prev) =>
      prev.map((t) => {
        if (t.id !== id) return t;
        if (!t.modified && !taskSnapshotsRef.current.has(id)) {
          taskSnapshotsRef.current.set(id, { ...t });
        }
        return { ...t, ...updates, modified: true };
      })
    );
  }, []);

  const updateTaskControl = useCallback((id: number, control: Task["control"], status: Task["status"]) => {
    setTasks((prev) =>
      prev.map((t) => (t.id === id ? { ...t, control, status } : t))
    );
  }, []);

  const saveTask = useCallback((id: number) => {
    setTasks((prev) =>
      prev.map((t) => (t.id === id ? { ...t, modified: false } : t))
    );
    taskSnapshotsRef.current.delete(id);
  }, []);

  const discardTask = useCallback((id: number) => {
    const snapshot = taskSnapshotsRef.current.get(id);
    if (snapshot) {
      setTasks((prev) =>
        prev.map((t) => (t.id === id ? { ...snapshot, modified: false } : t))
      );
      taskSnapshotsRef.current.delete(id);
    } else {
      setTasks((prev) =>
        prev.map((t) => (t.id === id ? { ...t, modified: false } : t))
      );
    }
  }, []);

  const saveAll = useCallback(() => {
    setTasks((prev) => prev.map((t) => ({ ...t, modified: false })));
  }, []);


  const selectedTask = tasks.find((t) => t.id === selectedId);
  const selectedModified = selectedTask?.modified ?? false;

  const handleSaveClick = useCallback(() => {
    if (selectedId !== null && selectedModified) {
      saveTask(selectedId);
    }
  }, [selectedId, selectedModified, saveTask]);

  const handleSelect = useCallback(
    (id: number | null) => {
      if (id === selectedId) return;
      if (selectedId !== null && selectedTask?.modified) {
        setPendingSelectId(id);
        setUnsavedPromptId(selectedId);
        return;
      }
      setSelectedId(id);
    },
    [selectedId, selectedTask?.modified]
  );

  return (
    <div className="flex flex-col h-full gap-3">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold tracking-wide text-primary">
          Планировщик задач
        </h1>
      </div>
      <SchedulerToolbar
        onAdd={addTask}
        onRemove={removeTask}
        onSave={handleSaveClick}
        onProperties={() => {}}
        hasSelection={selectedId !== null}
        hasModified={selectedModified}
      />
      <SchedulerFilters search={search} onSearchChange={setSearch} hasActiveFilters={hasActiveFilters} onResetFilters={resetAllFilters} />
      <SchedulerTable
        tasks={filteredTasks}
        allTasks={tasks}
        allTaskIds={tasks.map((t) => t.id)}
        selectedId={selectedId}
        onSelect={handleSelect}
        onUpdate={updateTask}
        onControlUpdate={updateTaskControl}
        columnFilters={columnFilters}
        onColumnFiltersChange={setColumnFilters}
      />

      {/* Save confirmation dialog */}
      <AlertDialog open={saveConfirmId !== null} onOpenChange={(open) => !open && setSaveConfirmId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Подтверждение сохранения</AlertDialogTitle>
            <AlertDialogDescription>
              Сохранить изменения для задачи <strong className="font-bold"> ID {saveConfirmId}</strong>?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (saveConfirmId !== null) {
                  saveTask(saveConfirmId);
                }
                setSaveConfirmId(null);
              }}
            >
              Сохранить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Unsaved changes on row switch dialog */}
      <AlertDialog open={unsavedPromptId !== null} onOpenChange={(open) => {
        if (!open) {
          setUnsavedPromptId(null);
          setPendingSelectId(null);
        }
      }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Несохранённые изменения</AlertDialogTitle>
            <AlertDialogDescription>
              Сохранить изменения для задачи <strong className="font-bold"> ID {unsavedPromptId}</strong>?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => {
              // Discard and switch - restore original values
              if (unsavedPromptId !== null) {
                discardTask(unsavedPromptId);
              }
              setSelectedId(pendingSelectId);
              setUnsavedPromptId(null);
              setPendingSelectId(null);
            }}>
              Не сохранять
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (unsavedPromptId !== null) {
                  saveTask(unsavedPromptId);
                }
                setSelectedId(pendingSelectId);
                setUnsavedPromptId(null);
                setPendingSelectId(null);
              }}
            >
              Сохранить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default Scheduler;
