export type TaskControl = "play" | "stop";

export interface Task {
  id: number;
  name: string;
  group: string;
  employee: string;
  control: TaskControl;
  dependency: number | null;
  status: "idle" | "running" | "success" | "error";
  notifications: boolean;
  logs: string;
  comment: string;
  properties: "set" | "unset";
  modified?: boolean;
}
