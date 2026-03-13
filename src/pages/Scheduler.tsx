import { useState, useCallback, useRef, useMemo, useEffect } from "react";
import { Task } from "@/types/task";
import { SchedulerToolbar } from "@/components/scheduler/SchedulerToolbar";
import { SchedulerTable } from "@/components/scheduler/SchedulerTable";
import { SchedulerFilters } from "@/components/scheduler/SchedulerFilters";
import { Button } from "@/components/ui/button";
import cronstrue from "cronstrue";
import "cronstrue/locales/ru";
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export type ColumnFilters = Record<string, Set<string>>;

type NotificationChannel = "" | "email" | "telegram";

type TaskPropertiesDraft = {
  launchDay: string;
  launchTime: string;
  endDay: string;
  endTime: string;
  fileType: "SQL" | "PY" | "BAT";
  connection: string;
  notificationChannel: NotificationChannel;
  notificationValue: string;
  cronHours: string;
  cronMinutes: string;
  cronWeekdays: string;
  cronMonthDays: string;
  cronMonths: string;
};

const Scheduler = () => {
  const apiBaseUrl = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [nextId, setNextId] = useState(1);
  const [saveConfirmId, setSaveConfirmId] = useState<number | null>(null);
  const [pendingSelectId, setPendingSelectId] = useState<number | null>(null);
  const [unsavedPromptId, setUnsavedPromptId] = useState<number | null>(null);
  const taskSnapshotsRef = useRef<Map<number, Task>>(new Map());
  const [search, setSearch] = useState("");
  const [columnFilters, setColumnFilters] = useState<ColumnFilters>({});
  const [propertiesOpen, setPropertiesOpen] = useState(false);
  const [propertiesDraft, setPropertiesDraft] = useState<TaskPropertiesDraft | null>(null);
  const [propertiesById, setPropertiesById] = useState<Record<number, TaskPropertiesDraft>>({});

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
  
  useEffect(() => {
    void (async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/tasks`);
        if (!response.ok) {
          throw new Error(`Не удалось загрузить задачи. Статус: ${response.status}`);
        }

        const fetchedTasks = (await response.json()) as Array<Omit<Task, "properties" | "modified">>;
        const sortedTasks = fetchedTasks
          .map((task) => ({ ...task, properties: "unset" as const, modified: false }))
          .sort((a, b) => a.id - b.id);

        setTasks(sortedTasks);
        const maxId = sortedTasks.length > 0 ? sortedTasks[sortedTasks.length - 1].id : 0;
        setNextId(maxId + 1);
        setSelectedId(null);
        taskSnapshotsRef.current.clear();
      } catch (error) {
        console.error(error);
      }
    })();
  }, [apiBaseUrl]);

  const resetAllFilters = useCallback(() => {
    setSearch("");
    setColumnFilters({});
  }, []);

  const buildDefaultProperties = () => {
    const now = new Date();
    const dateValue = now.toISOString().slice(0, 10);
    const timeValue = now.toTimeString().slice(0, 8);
    return {
      launchDay: dateValue,
      launchTime: timeValue,
      endDay: dateValue,
      endTime: timeValue,
      fileType: "SQL",
      connection: "",
      notificationChannel: "",
      notificationValue: "",
      cronHours: "*",
      cronMinutes: "*",
      cronWeekdays: "*",
      cronMonthDays: "*",
      cronMonths: "*",
    } satisfies TaskPropertiesDraft;
  };

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
    void (async () => {
      try {
        const deleteResponse = await fetch(`${apiBaseUrl}/tasks/${selectedId}`, {
          method: "DELETE",
        });

        if (!deleteResponse.ok && deleteResponse.status !== 404) {
          throw new Error(`Не удалось удалить задачу ${selectedId}. Статус: ${deleteResponse.status}`);
        }

        setTasks((prev) => prev.filter((t) => t.id !== selectedId));
        setPropertiesById((prev) => {
          const next = { ...prev };
          delete next[selectedId];
          return next;
        });
        taskSnapshotsRef.current.delete(selectedId);
        setSelectedId(null);
      } catch (error) {
        console.error(error);
      }
    })();
  }, [apiBaseUrl, selectedId]);

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

  // const saveTask = useCallback((id: number) => {
  //   setTasks((prev) =>
  //     prev.map((t) => (t.id === id ? { ...t, modified: false } : t))
  //   );
  //   taskSnapshotsRef.current.delete(id);
  // }, []);
   const saveTask = useCallback(async (id: number) => {
    const taskToSave = tasks.find((task) => task.id === id);
    if (!taskToSave) return;

    const taskPayload = {
      id: taskToSave.id,
      name: taskToSave.name,
      group: taskToSave.group,
      employee: taskToSave.employee,
      control: taskToSave.control,
      dependency: taskToSave.dependency,
      status: taskToSave.status,
      notifications: taskToSave.notifications,
      logs: taskToSave.logs,
      comment: taskToSave.comment,
    };

    try {
      const putResponse = await fetch(`${apiBaseUrl}/tasks/${id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(taskPayload),
      });

      if (!putResponse.ok && putResponse.status !== 404) {
        throw new Error(`Не удалось обновить задачу ${id}. Статус: ${putResponse.status}`);
      }

      if (putResponse.status === 404) {
        const postResponse = await fetch(`${apiBaseUrl}/tasks/${id}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(taskPayload),
        });

        if (!postResponse.ok) {
          throw new Error(`Не удалось создать задачу ${id}. Статус: ${postResponse.status}`);
        }
      }

      setTasks((prev) =>
        prev.map((t) => (t.id === id ? { ...t, modified: false } : t))
      );
      taskSnapshotsRef.current.delete(id);
    } catch (error) {
      console.error(error);
    }
  }, [apiBaseUrl, tasks]);

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
      void saveTask(selectedId);
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

  const handleOpenProperties = useCallback(() => {
    if (selectedId === null) return;
    const existing = propertiesById[selectedId];
    setPropertiesDraft(existing ? { ...existing } : buildDefaultProperties());
    setPropertiesOpen(true);
  }, [propertiesById, selectedId]);

  const handleSaveProperties = useCallback(() => {
    if (selectedId === null || !propertiesDraft) return;
    setPropertiesById((prev) => ({ ...prev, [selectedId]: propertiesDraft }));
    updateTask(selectedId, { properties: "set" });
    setPropertiesOpen(false);
  }, [propertiesDraft, selectedId, updateTask]);

  const enforceSingleSlash = (value: string) => {
    let out = "";
    let seen = false;
    for (const ch of value) {
      if (ch === "/") {
        if (seen) continue;
        seen = true;
      }
      out += ch;
    }
    return out;
  };
  const sanitizeCron = (value: string) => enforceSingleSlash(value.replace(/[^0-9,*/-]/g, ""));
  const normalizeEmptyToStar = (value: string) => (value.trim() === "" ? "*" : value);

  const clampCronValue = (value: string, max: number) => {
    let out = "";
    let currentNumber = "";
    const pushNumber = (num: string) => {
      if (num.length === 0) return "";
      const n = Number(num);
      if (Number.isNaN(n)) return "";
      if (n > max) return String(max);
      return num;
    };
    for (const ch of value) {
      if (/\d/.test(ch)) {
        currentNumber += ch;
      } else {
        out += pushNumber(currentNumber);
        currentNumber = "";
        out += ch;
      }
    }
    out += pushNumber(currentNumber);
    return out;
  };

  const sanitizeCronWithMax = (value: string, max: number) => clampCronValue(sanitizeCron(value), max);
  const normalizeStarUsage = (value: string) => {
    if (!value.includes("*")) return value;
    if (value === "*") return value;
    if (value === "*/") return value;
    const stepMatch = value.match(/^\*\/(\d+)$/);
    if (stepMatch) return `*/${stepMatch[1]}`;
    return "*";
  };

  const listValue = (value: string) => value.split(",").join(", ");

  const minutesDescription = (value: string) => {
    if (!value) return "Введите число от 1 до 59, '/' шаг, '-' диапазон, ',' перечисление";
    if (value === "*") return "Каждую минуту";
    const stepMatch = value.match(/^\*\/(\d+)$/);
    if (stepMatch) return `Каждую минуту с шагом ${stepMatch[1]}`;
    const startStepMatch = value.match(/^(\d+)\/(\d+)$/);
    if (startStepMatch) return `Начиная с ${startStepMatch[1]} минуты, каждую минуту с шагом ${startStepMatch[2]}`;
    const rangeStepMatch = value.match(/^(\d+)-(\d+)\/(\d+)$/);
    if (rangeStepMatch) {
    const start = parseInt(rangeStepMatch[1], 10);
    const end = parseInt(rangeStepMatch[2], 10);
    if (end <= start) {
      return "Ошибка: второе число должно быть больше первого";
    }}
    if (rangeStepMatch) return `С ${rangeStepMatch[1]} по ${rangeStepMatch[2]} минуту с шагом ${rangeStepMatch[3]}`;
    const rangeMatch = value.match(/^(\d+)-(\d+)$/);
    if (rangeMatch) {
    const start = parseInt(rangeMatch[1], 10);
    const end = parseInt(rangeMatch[2], 10);
    if (end <= start) {
      return "Ошибка: второе число должно быть больше первого";
    }}
    if (rangeMatch) return `С ${rangeMatch[1]} по ${rangeMatch[2]} минуту`;
    if (value.includes(",")) {
      return `На ${listValue(value)} минутах`;
    }
    if (/^\d+$/.test(value)) return `На ${value} минуте`;
    return "";
  };

  const hoursDescription = (value: string) => {
    if (!value) return "Введите число от 1 до 23, '/' шаг, '-' диапазон, ',' перечисление";
    if (value === "*") return "Каждый час";
    const stepMatch = value.match(/^\*\/(\d+)$/);
    if (stepMatch) return `Каждый час с шагом ${stepMatch[1]}`;
    const startStepMatch = value.match(/^(\d+)\/(\d+)$/);
    if (startStepMatch) return `Начиная с ${startStepMatch[1]} часов, каждый час с шагом ${startStepMatch[2]}`;
    const rangeStepMatch = value.match(/^(\d+)-(\d+)\/(\d+)$/);
    if (rangeStepMatch) return `С ${rangeStepMatch[1]} до ${rangeStepMatch[2]} часов с шагом ${rangeStepMatch[3]}`;
    const rangeMatch = value.match(/^(\d+)-(\d+)$/);
    if (rangeMatch) return `С ${rangeMatch[1]} до ${rangeMatch[2]} часов`;
    if (value.includes(",")) {
      return `В ${listValue(value)} часов`;
    }
    if (/^\d+$/.test(value)) return `В ${value} часов`;
    return "";
  };

  const monthDaysDescription = (value: string) => {
    if (!value) return "Введите число от 1 до 31, '/' шаг, '-' диапазон, ',' перечисление";
    if (value === "*") return "Каждый день месяца";
    const stepMatch = value.match(/^\*\/(\d+)$/);
    if (stepMatch) return `Каждый день месяца с шагом ${stepMatch[1]}`;
    const startStepMatch = value.match(/^(\d+)\/(\d+)$/);
    if (startStepMatch) return `Начиная с ${startStepMatch[1]} числа, каждый день месяца с шагом ${startStepMatch[2]}`;
    const rangeStepMatch = value.match(/^(\d+)-(\d+)\/(\d+)$/);
    if (rangeStepMatch) return `С ${rangeStepMatch[1]} по ${rangeStepMatch[2]} число с шагом ${rangeStepMatch[3]}`;
    const rangeMatch = value.match(/^(\d+)-(\d+)$/);
    if (rangeMatch) return `С ${rangeMatch[1]} по ${rangeMatch[2]} число`;
    if (value.includes(",")) {
      return `${listValue(value)} числа`;
    }
    if (/^\d+$/.test(value)) return `${value}-го числа`;
    return "";
  };

  const monthsDescription = (value: string) => {
    if (!value) return "Введите число от 1 до 12, '/' шаг, '-' диапазон, ',' перечисление";
    if (value === "*") return "Каждый месяц";
    const stepMatch = value.match(/^\*\/(\d+)$/);
    if (stepMatch) return `Каждый месяц с шагом ${stepMatch[1]}`;
    const startStepMatch = value.match(/^(\d+)\/(\d+)$/);
    if (startStepMatch) return `Начиная с ${startStepMatch[1]} месяца, каждый месяц с шагом ${startStepMatch[2]}`;
    const rangeStepMatch = value.match(/^(\d+)-(\d+)\/(\d+)$/);
    if (rangeStepMatch) return `С ${rangeStepMatch[1]} по ${rangeStepMatch[2]} месяц с шагом ${rangeStepMatch[3]}`;
    const rangeMatch = value.match(/^(\d+)-(\d+)$/);
    if (rangeMatch) return `С ${rangeMatch[1]} по ${rangeMatch[2]} месяц`;
    if (value.includes(",")) {
      return `В ${listValue(value)} месяце`;
    }
    if (/^\d+$/.test(value)) return `В ${value} месяце`;
    return "";
  };

  const weekdaysDescription = (value: string) => {
    if (!value) return "Введите число от 1 до 7, '/' шаг, '-' диапазон, ',' перечисление";
    if (value === "*") return "Каждый день недели";
    const stepMatch = value.match(/^\*\/(\d+)$/);
    if (stepMatch) return `Каждый день недели с шагом ${stepMatch[1]}`;
    const startStepMatch = value.match(/^(\d+)\/(\d+)$/);
    if (startStepMatch) return `Начиная с ${startStepMatch[1]} дня недели, каждый день недели с шагом ${startStepMatch[2]}`;
    const rangeStepMatch = value.match(/^(\d+)-(\d+)\/(\d+)$/);
    if (rangeStepMatch) return `С ${rangeStepMatch[1]} по ${rangeStepMatch[2]} день недели с шагом ${rangeStepMatch[3]}`;
    const rangeMatch = value.match(/^(\d+)-(\d+)$/);
    if (rangeMatch) return `С ${rangeMatch[1]} по ${rangeMatch[2]} день недели`;
    if (value.includes(",")) {
      return `В ${listValue(value)} день недели`;
    }
    if (/^\d+$/.test(value)) return `В ${value} день недели`;
    return "";
  };

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
        onProperties={handleOpenProperties}
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

      <Dialog open={propertiesOpen} onOpenChange={setPropertiesOpen}>
        <DialogContent
          className="max-w-2xl"
          onEscapeKeyDown={(e) => e.preventDefault()}
          onPointerDownOutside={(e) => e.preventDefault()}
          onInteractOutside={(e) => e.preventDefault()}
        >
          <DialogHeader className="flex-row items-center justify-between space-y-0 mb-3">
            <DialogTitle>
              {selectedId !== null ? `Свойства задачи ID ${selectedId}` : "Свойства задачи"}
            </DialogTitle>
          </DialogHeader>
          <div className="grid gap-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="grid gap-2">
                <Label htmlFor="launch-day">День запуска</Label>
                <Input
                  id="launch-day"
                  type="date"
                  className="bg-white"
                  value={propertiesDraft?.launchDay ?? ""}
                  onChange={(e) => propertiesDraft && setPropertiesDraft({ ...propertiesDraft, launchDay: e.target.value })}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="launch-time">Время запуска</Label>
                <Input
                  id="launch-time"
                  type="text"
                  inputMode="numeric"
                  placeholder="HH:MM:SS"
                  className="bg-white"
                  value={propertiesDraft?.launchTime ?? ""}
                  onChange={(e) => {
                    if (!propertiesDraft) return;
                    const next = e.target.value.replace(/[^0-9:]/g, "");
                    setPropertiesDraft({ ...propertiesDraft, launchTime: next });
                  }}
                />
              </div>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="grid gap-2">
                <Label htmlFor="end-day">День окончания</Label>
                <Input
                  id="end-day"
                  type="date"
                  className="bg-white"
                  value={propertiesDraft?.endDay ?? ""}
                  onChange={(e) => propertiesDraft && setPropertiesDraft({ ...propertiesDraft, endDay: e.target.value })}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="end-time">Время окончания</Label>
                <Input
                  id="end-time"
                  type="text"
                  inputMode="numeric"
                  placeholder="HH:MM:SS"
                  className="bg-white"
                  value={propertiesDraft?.endTime ?? ""}
                  onChange={(e) => {
                    if (!propertiesDraft) return;
                    const next = e.target.value.replace(/[^0-9:]/g, "");
                    setPropertiesDraft({ ...propertiesDraft, endTime: next });
                  }}
                />
              </div>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="grid gap-2">
                <Label>Файл</Label>
                <Select
                  value={propertiesDraft?.fileType ?? "SQL"}
                  onValueChange={(value) => propertiesDraft && setPropertiesDraft({ ...propertiesDraft, fileType: value as TaskPropertiesDraft["fileType"] })}
                >
                  <SelectTrigger className="bg-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="SQL">SQL</SelectItem>
                    <SelectItem value="PY">PY</SelectItem>
                    <SelectItem value="BAT">BAT</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="connection">Подключение</Label>
                <Input
                  id="connection"
                  placeholder="-"
                  value={propertiesDraft?.connection ?? ""}
                  disabled
                  className="bg-white"
                />
              </div>
            </div>
            <div className="grid gap-2">
              <Label>Уведомления</Label>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <Select
                  value={propertiesDraft?.notificationChannel ?? ""}
                  onValueChange={(value) =>
                    propertiesDraft &&
                    setPropertiesDraft({
                      ...propertiesDraft,
                      notificationChannel: value as NotificationChannel,
                      notificationValue: value ? propertiesDraft.notificationValue : "",
                    })
                  }
                >
                  <SelectTrigger className="bg-white">
                    <SelectValue placeholder="Выбрать" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="email">Email</SelectItem>
                    <SelectItem value="telegram">Telegram</SelectItem>
                  </SelectContent>
                </Select>
                {propertiesDraft?.notificationChannel ? (
                  <Input
                    placeholder={propertiesDraft.notificationChannel === "email" ? "Email" : "@username"}
                    value={propertiesDraft.notificationValue}
                    onChange={(e) =>
                      propertiesDraft &&
                      setPropertiesDraft({ ...propertiesDraft, notificationValue: e.target.value })
                    }
                    className="bg-white"
                  />
                ) : (
                  <Input placeholder="Не выбрано" disabled className="bg-white" />
                )}
              </div>
            </div>
            <div className="grid gap-2">
              <div className="grid grid-cols-[minmax(160px,1.3fr)_minmax(100px,1fr)_minmax(220px,2fr)] items-center gap-3 text-sm font-medium text-muted-foreground text-center">
                <div>Поле ввода</div>
                <div>Параметр</div>
                <div>Описание</div>
              </div>
             
              <div className="grid grid-cols-[minmax(160px,1.3fr)_minmax(100px,1fr)_minmax(220px,2fr)] items-center gap-3">
                <Input
                  value={propertiesDraft?.cronMinutes ?? ""}
                  className="bg-white"
                  onChange={(e) =>
                    propertiesDraft &&
                    setPropertiesDraft({ ...propertiesDraft, cronMinutes: normalizeStarUsage(sanitizeCronWithMax(e.target.value, 59)) })
                  }
                  onBlur={(e) =>
                    propertiesDraft &&
                    setPropertiesDraft({ ...propertiesDraft, cronMinutes: normalizeEmptyToStar(e.target.value) })
                  }
                />
                <div className="text-sm">Минута</div>
                <div className="text-sm text-muted-foreground">
                  {minutesDescription(propertiesDraft?.cronMinutes ?? "")}
                </div>
              </div>
               <div className="grid grid-cols-[minmax(160px,1.3fr)_minmax(100px,1fr)_minmax(220px,2fr)] items-center gap-3">
                <Input
                  value={propertiesDraft?.cronHours ?? ""}
                  className="bg-white"
                  onChange={(e) =>
                    propertiesDraft &&
                    setPropertiesDraft({ ...propertiesDraft, cronHours: normalizeStarUsage(sanitizeCronWithMax(e.target.value, 23)) })
                  }
                  onBlur={(e) =>
                    propertiesDraft &&
                    setPropertiesDraft({ ...propertiesDraft, cronHours: normalizeEmptyToStar(e.target.value) })
                  }
                />
                <div className="text-sm">Час</div>
                <div className="text-sm text-muted-foreground">
                  {hoursDescription(propertiesDraft?.cronHours ?? "")}
                </div>
              </div>
              <div className="grid grid-cols-[minmax(160px,1.3fr)_minmax(100px,1fr)_minmax(220px,2fr)] items-center gap-3">
                <Input
                  value={propertiesDraft?.cronMonthDays ?? ""}
                  className="bg-white"
                  onChange={(e) =>
                    propertiesDraft &&
                    setPropertiesDraft({ ...propertiesDraft, cronMonthDays: normalizeStarUsage(sanitizeCronWithMax(e.target.value, 31)) })
                  }
                  onBlur={(e) =>
                    propertiesDraft &&
                    setPropertiesDraft({ ...propertiesDraft, cronMonthDays: normalizeEmptyToStar(e.target.value) })
                  }
                />
                <div className="text-sm">День месяца</div>
                <div className="text-sm text-muted-foreground">
                  {monthDaysDescription(propertiesDraft?.cronMonthDays ?? "")}
                </div>
              </div>              
              <div className="grid grid-cols-[minmax(160px,1.3fr)_minmax(100px,1fr)_minmax(220px,2fr)] items-center gap-3">
                <Input
                  value={propertiesDraft?.cronMonths ?? ""}
                  className="bg-white"
                  onChange={(e) =>
                    propertiesDraft &&
                    setPropertiesDraft({ ...propertiesDraft, cronMonths: normalizeStarUsage(sanitizeCronWithMax(e.target.value, 12)) })
                  }
                  onBlur={(e) =>
                    propertiesDraft &&
                    setPropertiesDraft({ ...propertiesDraft, cronMonths: normalizeEmptyToStar(e.target.value) })
                  }
                />
                <div className="text-sm">Месяц</div>
                <div className="text-sm text-muted-foreground">
                  {monthsDescription(propertiesDraft?.cronMonths ?? "")}
                </div>
              </div>
              <div className="grid grid-cols-[minmax(160px,1.3fr)_minmax(100px,1fr)_minmax(220px,2fr)] items-center gap-3">
                <Input
                  value={propertiesDraft?.cronWeekdays ?? ""}
                  className="bg-white"
                  onChange={(e) =>
                    propertiesDraft &&
                    setPropertiesDraft({ ...propertiesDraft, cronWeekdays: normalizeStarUsage(sanitizeCronWithMax(e.target.value, 7)) })
                  }
                  onBlur={(e) =>
                    propertiesDraft &&
                    setPropertiesDraft({ ...propertiesDraft, cronWeekdays: normalizeEmptyToStar(e.target.value) })
                  }
                />
                <div className="text-sm">День недели</div>
                <div className="text-sm text-muted-foreground">
                  {weekdaysDescription(propertiesDraft?.cronWeekdays ?? "")}
                </div>
              </div>
            </div>
          </div>
          <div className="rounded-md border border-border bg-background p-3 text-sm">
            {(() => {
              const safe = (v: string | undefined) => (v && v.trim() ? v.trim() : "*");
              const cronExpression = `${safe(propertiesDraft?.cronMinutes)} ${safe(propertiesDraft?.cronHours)} ${safe(propertiesDraft?.cronMonthDays)} ${safe(propertiesDraft?.cronMonths)} ${safe(propertiesDraft?.cronWeekdays)}`;
              let cronText = "";
              try {
                const rawLocale = typeof navigator !== "undefined" && navigator.language ? navigator.language : "ru";
                cronText = cronstrue.toString(cronExpression, { 
                                              locale: "ru",
                                              verbose: true,
                                              dayOfWeekStartIndexZero: true,
                                              monthStartIndexZero: false,
                                              use24HourTimeFormat: true
                                            });
              } catch {
                cronText = "Невозможно разобрать cron-выражение";
              }
              return (
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                  <div className="sm:col-span-1 flex flex-col gap-1">
                    <span className="text-muted-foreground">Cron выражение</span>
                    <span className="font-mono">{cronExpression}</span>
                  </div>
                  <div className="sm:col-span-2 flex flex-col gap-1 ml-10">
                    <span className="text-muted-foreground">Описание сценария</span>
                    <span>{cronText}</span>
                  </div>
                </div>
              );
            })()}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPropertiesOpen(false)}>
              Отмена
            </Button>
            <Button onClick={handleSaveProperties} disabled={!propertiesDraft}>
              Сохранить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

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
                  void saveTask(saveConfirmId);
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
                  void saveTask(unsavedPromptId);
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
