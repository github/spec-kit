import { ListrRenderer } from '../interfaces/renderer.interface';
import { Task } from '../lib/task';
export declare class SilentRenderer implements ListrRenderer {
    tasks: Task<any, typeof SilentRenderer>[];
    options: typeof SilentRenderer['rendererOptions'];
    /** designates whether this renderer can output to a non-tty console */
    static nonTTY: boolean;
    /** renderer options for the silent renderer */
    static rendererOptions: never;
    /** per task options for the silent renderer */
    static rendererTaskOptions: never;
    constructor(tasks: Task<any, typeof SilentRenderer>[], options: typeof SilentRenderer['rendererOptions']);
    render(): void;
    end(): void;
}
