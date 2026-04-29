export interface TaskOut {
  task_id: number;           
  task_name: string;         
  on_control: 'on' | 'off'; 
  owner: string;            
  task_group: string | null; 
  schedule_cron: string | null;  
  schedule_depend: string | null; 
  next_run_at: string | null;
  task_deps_id: number | null; 
  status: string;           
  notifications: boolean;   
  comment: string | null;  
  last_run_at: string | null;
  edit_expire_at: string;
  run_expire_at: string; 
  TTL_EDIT_SECONDS: number;
}

// Connections
export type ConnType = 'postgresql' | 'mysql' | 'mariadb' | 'mssql' | 'oracle' | 'sqlite' | 'teradata';



export interface ConnectionOut {
  id: number;
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

// TaskProperties
export type TaskType = 'sql' | 'py' | 'bat' ;



export interface TaskPropsOut {
  task_id: number;
  from_dt: string | null;
  until_dt: string | null;
  connection_id: number | null;
  cron_expression: string | null;
  task_type: TaskType;
  storage_path: string;
  file_names: string[] | null;
  email: string | null;
  tg_chat_id: string | null;
  conn_name: string | null;
}

export interface TaskPropsIn extends TaskPropsOut {
  root_folder: string;
}


// export interface PropFile {
//   id: number;
//   task_id: number;
//   file_path: string;
//   file_name: string;
//   change_dt: string;
// }

export interface TaskRunningOut {
  task_name: string | null;
  task_id: number;
  parent_id: number | null;
  trigger_mode: string | null;
  schedule_dt: string;  
  created_dt: string;  
  worker_id: number | null;
  started_str: string | null;
  finished_str: string | null;
  duration: string | null;
  attempt_count: number | null;
  next_retry_at: string | null;
  status: string | null;
}

export interface TaskLogOut {
  task_id: number;
  file_name: string | null;
  log_text: string | null;
  pid_id: number | null;
  created_dt: string | null;
}