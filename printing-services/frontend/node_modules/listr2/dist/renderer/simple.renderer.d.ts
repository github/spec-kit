import { ListrEventType } from '../constants/event.constants';
import { ListrEventFromType } from '../interfaces/listr.interface';
import { ListrRenderer } from '../interfaces/renderer.interface';
import { Task } from '../lib/task';
/**
 * This is the default renderer which is neither verbose or updating.
 * It provides short output like update renderer, but does not disturb
 * stdin during execution of listr tasks
 */
export declare class SimpleRenderer implements ListrRenderer {
    readonly tasks: Task<any, typeof SimpleRenderer>[];
    options: typeof SimpleRenderer['rendererOptions'];
    static nonTTY: boolean;
    static rendererOptions: {
        /**
         * if true this will add
         * timestamp at the begin of the rendered line
         *
         * @example
         *
         * ```bash
         * [12:33:44] ✔ Do something important
         * ```
         *
         * @default false
         */
        prefixWithTimestamp?: boolean;
        /**
         * choose between process.stdout and process.stderr
         *
         * @default stdout
         */
        output?: 'stdout' | 'stderr';
    };
    static rendererTaskOptions: never;
    /**
     * Event type renderer map contains functions to process different task events
     */
    eventTypeRendererMap: Partial<{
        [P in ListrEventType]: (t: Task<any, typeof SimpleRenderer>, event: ListrEventFromType<P>) => void;
    }>;
    constructor(tasks: Task<any, typeof SimpleRenderer>[], options: typeof SimpleRenderer['rendererOptions']);
    static now(): Date;
    static formatTitle(task?: Task<any, typeof SimpleRenderer>): string;
    log(output?: string): void;
    end(): void;
    render(tasks?: Task<any, typeof SimpleRenderer>[]): void;
}
