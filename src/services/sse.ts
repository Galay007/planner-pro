import {Logger} from '../utils/logger'

const SSE_URL = 'http://192.168.1.67:8000/sse';

let eventSource: EventSource | null = null;

export interface SSEHandlers {
  onError: (error: Event) => void;
  onOpen: () => void;
  onRefresh: () => void;
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

  eventSource.addEventListener('task_update', () => {
    Logger.info('[SSE] update event received');
    handlers.onRefresh?.();
    // setTimeout(() => handlers.onRefresh?.(), 200);
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
