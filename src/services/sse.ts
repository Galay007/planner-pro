import type { TasksPayload, TaskRunningsPayload } from '../types';

const SSE_URL = 'http://192.168.1.67:8000/sse';

let eventSource: EventSource | null = null;

export interface SSEHandlers {
  onTasks?: (data: TasksPayload) => void;
  onTaskRunnings?: (data: TaskRunningsPayload) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  onRefresh?: () => void;
}

export function connectSSE(handlers: SSEHandlers): EventSource {
  if (eventSource) {
    eventSource.close();
  }

  eventSource = new EventSource(SSE_URL);

  eventSource.onopen = () => {
    console.log('[SSE] Connection opened');
    handlers.onOpen?.();
  };

  eventSource.onerror = (error) => {
    console.error('[SSE] Connection error', error);
    handlers.onError?.(error);
  };

  // --- Event: tasks ---
  eventSource.addEventListener('tasks', (event: MessageEvent) => {
    try {
      // TODO: validate/parse real data structure once API schema is known
      const data: TasksPayload = JSON.parse(event.data);
      console.log('[SSE] tasks event received', data);
      handlers.onTasks?.(data);
    } catch (e) {
      console.error('[SSE] Failed to parse tasks event', e);
    }
  });

  // --- Event: task_runnings ---
  eventSource.addEventListener('task_runnings', (event: MessageEvent) => {
    try {
      // TODO: validate/parse real data structure once API schema is known
      const data: TaskRunningsPayload = JSON.parse(event.data);
      console.log('[SSE] task_runnings event received', data);
      handlers.onTaskRunnings?.(data);
    } catch (e) {
      console.error('[SSE] Failed to parse task_runnings event', e);
    }
  });


  eventSource.addEventListener('task_update', () => {
    console.log('[SSE] update event received');
    handlers.onRefresh?.();
  });

  return eventSource;
}

export function disconnectSSE(): void {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
    console.log('[SSE] Connection closed');
  }
}
