import axios from 'axios';
import type { TaskOut, ConnectionOut, ConnectionIn, TaskPropsOut, TaskRunningOut } from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ApiResult {
  status: number;
  detail?: string;
}

function extractDetail(data: unknown): string | undefined {
  if (data && typeof data === 'object' && 'detail' in data) {
    return String((data as Record<string, unknown>).detail);
  }
  return undefined;
}

// Tasks
export async function getTasks(): Promise<{ data: TaskOut[] } & ApiResult> {
  const response = await api.get<TaskOut[]>('/tasks');
  return { data: response.data, status: response.status };
}

export async function startTask(taskId: number): Promise<ApiResult> {
  const response = await api.put(`/tasks/on/${taskId}`);
  return { status: response.status, detail: extractDetail(response.data) };
}

export async function stopTask(taskId: number): Promise<ApiResult> {
  const response = await api.put(`/tasks/off/${taskId}`);
  return { status: response.status, detail: extractDetail(response.data) };
}

export async function startEdit(taskId: number): Promise<ApiResult> {
  const response = await api.put(`/tasks/start_edit/${taskId}`);
  return { status: response.status, detail: extractDetail(response.data) };
}

export async function sendHeartBeat(taskId: number): Promise<ApiResult> {
  const response = await api.put(`/tasks/heart_beat/${taskId}`);
  return { status: response.status, detail: extractDetail(response.data) };
}

export async function cancelEdit(taskId: number): Promise<ApiResult> {
  const response = await api.put(`/tasks/cancel_edit/${taskId}`);
  return { status: response.status, detail: extractDetail(response.data) };
}

export async function oneTimeRun(taskId: number): Promise<ApiResult> {
  const response = await api.put(`/tasks/run/${taskId}`);
  return { status: response.status, detail: extractDetail(response.data) };
}

export async function saveTask(taskId: number, body: Partial<TaskOut>): Promise<ApiResult> {
  const response = await api.put(`/tasks/save/${taskId}`, body);
  return { status: response.status, detail: extractDetail(response.data) };
}

export async function deleteTask(taskId: number): Promise<ApiResult> {
  const response = await api.delete(`/tasks/${taskId}`);
  return { status: response.status, detail: extractDetail(response.data) };
}

export async function getMaxTaskId(): Promise<number> {
  const response = await api.get<number>('/tasks/max_task_id');
  return response.data;
}

export async function createTask(taskId: number): Promise<ApiResult> {
  const response = await api.post('/tasks', {
    task_id: taskId,
    task_name: '-',
    owner: '-',
  });
  return { status: response.status, detail: extractDetail(response.data) };
}

// TaskProperties

export async function getProps(): Promise<{ data: TaskPropsOut[] } & ApiResult> {
  const response = await api.get<TaskPropsOut[]>('/task_properties');
  return { data: response.data, status: response.status };
}

export async function getProp(taskId: number): Promise<{ data: TaskPropsOut } & ApiResult> {
  const response = await api.get<TaskPropsOut>(`/task_properties/${taskId}`);
  return { data: response.data, status: response.status };
}

export async function createProp(formData: FormData): Promise<{ data: TaskPropsOut } & ApiResult> {
  const response = await api.post<TaskPropsOut>('/task_properties', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return { data: response.data, status: response.status, detail: extractDetail(response.data) };
}

export async function saveProp(taskId: number, formData: FormData): Promise<{ data: TaskPropsOut } & ApiResult> {
  const response = await api.put<TaskPropsOut>(`/task_properties/${taskId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return { data: response.data, status: response.status, detail: extractDetail(response.data) };
}

// Connections
export async function getConnections(): Promise<{ data: ConnectionOut[] } & ApiResult> {
  const response = await api.get<ConnectionOut[]>('/connections');
  return { data: response.data, status: response.status };
}

export async function getConnection(name: string): Promise<{ data: ConnectionOut } & ApiResult> {
  const response = await api.get<ConnectionOut>(`/connections/${name}`);
  return { data: response.data, status: response.status };
}

export async function createConnection(body: Omit<ConnectionIn, 'id'>): Promise<ApiResult> {
  const response = await api.post('/connections', body);
  return { status: response.status, detail: extractDetail(response.data) };
}

export async function deleteConnection(name: string): Promise<ApiResult> {
  const response = await api.delete(`/connections/${name}`);
  return { status: response.status, detail: extractDetail(response.data) };
}

export async function testConnection(body: Partial<ConnectionIn>): Promise<ApiResult> {
  const response = await api.post(`/connections/test`, body);
  return { status: response.status, detail: extractDetail(response.data) };
}

// TaskRunnings
export async function getTaskRunnings(): Promise<{ data: TaskRunningOut[] } & ApiResult> {
  const response = await api.get<TaskRunningOut[]>('/task_runnings');
  return { data: response.data, status: response.status };
}

export function parseApiError(e: unknown): ApiResult {
  if (axios.isAxiosError(e)) {
    return {
      status: e.response?.status ?? 0,
      detail: extractDetail(e.response?.data) ?? e.message,
    };
  }
  return { status: 0, detail: String(e) };
}

export default api;