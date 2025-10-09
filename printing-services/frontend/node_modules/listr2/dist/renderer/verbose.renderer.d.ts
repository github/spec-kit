import { ListrRenderer } from '../interfaces/renderer.interface';
import { Task } from '../lib/task';
import { Logger } from '../utils/logger';
export declare class VerboseRenderer implements ListrRenderer {
    tasks: Task<any, typeof VerboseRenderer>[];
    options: typeof VerboseRenderer['rendererOptions'];
    /** designates whether this renderer can output to a non-tty console */
    static nonTTY: boolean;
    /** renderer options for the verbose renderer */
    static rendererOptions: ({
        /**
             * useIcons instead of text for log level
             * @default false
             */
        useIcons?: boolean;
        /**
             * log tasks with empty titles
             * @default true
             */
        logEmptyTitle?: boolean;
        /**
             * log title changes
             * @default true
             */
        logTitleChange?: boolean;
        /**
             * show duration for all tasks
             */
        showTimer?: boolean;
    } & {
        /**
             * inject a custom logger
             */
        logger?: new (...args: any) => Logger;
        /**
             * inject options to custom logger
             */
        options?: any;
    });
    /** per task options for the verbose renderer */
    static rendererTaskOptions: never;
    private logger;
    constructor(tasks: Task<any, typeof VerboseRenderer>[], options: typeof VerboseRenderer['rendererOptions']);
    render(): void;
    end(): void;
    private verboseRenderer;
}
