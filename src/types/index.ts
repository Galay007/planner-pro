export interface TaskOut {
  task_id: number;           
  task_name: string;         
  on_control: 'on' | 'off'; 
  owner: string;            
  task_group: string | null; 
  schedule: string | null;  
  task_deps_id: number | null; 
  status: string;           
  notifications: boolean;   
  comment: string | null;   
}

// TaskRunning entity from task_runnings SSE event — structure TBD
export interface TaskRunning {
  task_id: number;
  started_at: string;
  status: string;
}

export type TasksPayload = TaskOut[];
export type TaskRunningsPayload = TaskRunning[];

// Connections
export type ConnType = 'postgresql' | 'mysql' | 'mariadb' | 'mssql' | 'oracle' | 'sqlite' | 'teradata';

export interface ConnectionOut {
  name: string;
  conn_type: ConnType;
  host: string | null;
  port: number | null;
  db_name: string | null;
  login: string | null;
  db_path: string | null;
}

export interface ConnectionIn extends ConnectionOut {
  pass_str: string | null;
}

export interface ServerMessage {
  status: number;
  text: string;
  detail?: string;
  ok: boolean;
}
