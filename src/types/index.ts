// TaskOut from backend
export interface TaskOut {
  task_id: number;           // ID
  task_name: string;         // Задача
  on_control: 'on' | 'off'; // Управление
  owner: string;             // Автор
  task_group: string | null; // Группа
  schedule: string | null;   // След. запуск
  task_deps_id: number | null; // Связь с ID
  status: string;            // Статус
  notifications: boolean;    // Уведомл.
  comment: string | null;    // Комментарий
}

// TaskRunning entity from task_runnings SSE event — structure TBD
export interface TaskRunning {
  task_id: number;
  started_at: string;
  status: string;
}

export type TasksPayload = TaskOut[];
export type TaskRunningsPayload = TaskRunning[];
