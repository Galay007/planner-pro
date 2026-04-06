import axios from 'axios';
import type { TaskOut } from '../types';

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

export async function getTasks(): Promise<{ data: TaskOut[] } & ApiResult> {
  const response = await api.get<TaskOut[]>('/tasks');
  return { data: response.data, status: response.status };
}

export async function startTask(taskId: number): Promise<ApiResult> {
  const response = await api.put(`/tasks/${taskId}/on`);
  return { status: response.status, detail: extractDetail(response.data) };
}

export async function stopTask(taskId: number): Promise<ApiResult> {
  const response = await api.put(`/tasks/${taskId}/off`);
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

/** Извлекает status и detail из axios-ошибки */
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