export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export class Logger {
    private static formatTime(date: Date = new Date()): string {
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        const ms = String(date.getMilliseconds()).padStart(3, '0');
        return `${hours}:${minutes}:${seconds}.${ms}`;
    }

    private static prefix(level: LogLevel): string {
        return `[${Logger.formatTime()}] [${level.toUpperCase()}]`;
    }

    static debug(message: string, ...args: unknown[]): void {
        console.debug(Logger.prefix('debug'), message, ...args);
    }

    static info(message: string, ...args: unknown[]): void {
        console.info(Logger.prefix('info'), message, ...args);
    }

    static warn(message: string, ...args: unknown[]): void {
        console.warn(Logger.prefix('warn'), message, ...args);
    }

    static error(message: string, error?: unknown): void {
        console.error(Logger.prefix('error'), message, error || '');
    }
}