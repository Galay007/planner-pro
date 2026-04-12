export interface TaskOut {
  task_id: number;           
  task_name: string;         
  on_control: 'on' | 'off'; 
  owner: string;            
  task_group: string | null; 
  schedule: string | null;  
  next_run_at: string | null;
  task_deps_id: number | null; 
  status: string;           
  notifications: boolean;   
  comment: string | null;  
  last_run_at: string | null;
  edit_expire_at: string;
  run_expire_at: string; 
}

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
