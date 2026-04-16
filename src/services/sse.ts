import {Logger} from '../utils/logger'

const SSE_URL = 'http://192.168.1.67:8000/sse';

let eventSource: EventSource | null = null;

export interface SSEHandlers {
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
    console.log('[SSE] connection opened');
    handlers.onOpen?.();
  };

  eventSource.onerror = (error) => {
    Logger.error('[SSE] connection error', error);
    handlers.onError?.(error);
  };

  // eventSource.onmessage = (event) => {
  //   Logger.info('[SSE] message received', event.data);
  // };

  // eventSource.addEventListener('connected', (event) => {
  //   Logger.info('[SSE] connected event received', event);
  // });

  eventSource.addEventListener('task_update', () => {
    Logger.info('[SSE] task_update event received');
    handlers.onRefresh?.();
  });

  return eventSource;
}

export function disconnectSSE(): void {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
    Logger.info('[SSE] connection closed');
  }
}