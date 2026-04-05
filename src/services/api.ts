import axios from 'axios';
import type { TaskOut } from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function getTasks(): Promise<TaskOut[]> {
  const response = await api.get<TaskOut[]>('/tasks');
  return response.data;
}

export async function startTask(taskId: number): Promise<void> {
  await api.put(`/tasks/${taskId}/on`);
}

export async function stopTask(taskId: number): Promise<void> {
  await api.put(`/tasks/${taskId}/off`);
}

export async function deleteTask(taskId: number): Promise<void> {
  await api.delete(`/tasks/${taskId}`);
}

export default api;
