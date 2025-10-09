import { LogLevels } from './logger.constants';
import { LoggerOptions } from './logger.interface';
/**
 * A internal logger for using in the verbose renderer mostly.
 */
export declare class Logger {
    private options?;
    constructor(options?: LoggerOptions);
    fail(message: string): void;
    skip(message: string): void;
    success(message: string): void;
    data(message: string): void;
    start(message: string): void;
    title(message: string): void;
    retry(message: string): void;
    rollback(message: string): void;
    protected parseMessage(level: LogLevels, message: string): string;
    protected logColoring({ level, message }: {
        level: LogLevels;
        message: string;
    }): string;
    private wrapInBrackets;
}
