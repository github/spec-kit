import { Subject } from 'rxjs';
import { TaskWrapper } from './task-wrapper';
import { ListrTaskState } from '../constants/state.constants';
import { PromptError } from '../interfaces/listr-error.interface';
import { ListrEvent, ListrOptions, ListrTask, ListrTaskResult } from '../interfaces/listr.interface';
import { ListrGetRendererOptions, ListrGetRendererTaskOptions, ListrRendererFactory } from '../interfaces/renderer.interface';
import { Listr } from '../listr';
import { PromptInstance } from '../utils/prompt.interface';
/**
 * Create a task from the given set of variables and make it runnable.
 */
export declare class Task<Ctx, Renderer extends ListrRendererFactory> extends Subject<ListrEvent> {
    listr: Listr<Ctx, any, any>;
    tasks: ListrTask<Ctx, any>;
    options: ListrOptions;
    rendererOptions: ListrGetRendererOptions<Renderer>;
    /** Unique id per task, randomly generated in the uuid v4 format */
    id: string;
    /** The current state of the task. */
    state: string;
    /** The task object itself, to further utilize it. */
    task: (ctx: Ctx, task: TaskWrapper<Ctx, Renderer>) => void | ListrTaskResult<Ctx>;
    /** Extend current task with multiple subtasks. */
    subtasks: Task<Ctx, any>[];
    /** Title of the task */
    title?: string;
    /** Untouched unchanged title of the task */
    initialTitle?: string;
    /** Output data from the task. */
    output?: string;
    /** Skip current task. */
    skip: boolean | string | ((ctx: Ctx) => boolean | string | Promise<boolean | string>);
    /** Current retry number of the task if retrying */
    retry?: {
        count: number;
        withError?: any;
    };
    /**
     * A channel for messages.
     *
     * This requires a separate channel for messages like error, skip or runtime messages to further utilize in the renderers.
     */
    message: {
        /** Run time of the task, if it has been successfully resolved. */
        duration?: number;
        /** Error message of the task, if it has been failed. */
        error?: string;
        /** Skip message of the task, if it has been skipped. */
        skip?: string;
        /** Rollback message of the task, if the rollback finishes */
        rollback?: string;
        /** Retry messages */
        retry?: {
            count: number;
            withError?: any;
        };
    };
    /** Per task options for the current renderer of the task. */
    rendererTaskOptions: ListrGetRendererTaskOptions<Renderer>;
    /** This will be triggered each time a new render should happen. */
    renderHook$: Subject<void>;
    prompt: undefined | PromptInstance | PromptError;
    private enabled;
    private enabledFn;
    constructor(listr: Listr<Ctx, any, any>, tasks: ListrTask<Ctx, any>, options: ListrOptions, rendererOptions: ListrGetRendererOptions<Renderer>);
    set state$(state: ListrTaskState);
    set output$(data: string);
    set message$(data: Task<Ctx, Renderer>['message']);
    set title$(title: string);
    /**
     * A function to check whether this task should run at all via enable.
     */
    check(ctx: Ctx): Promise<void>;
    /** Returns whether this task has subtasks. */
    hasSubtasks(): boolean;
    /** Returns whether this task is in progress. */
    isPending(): boolean;
    /** Returns whether this task is skipped. */
    isSkipped(): boolean;
    /** Returns whether this task has been completed. */
    isCompleted(): boolean;
    /** Returns whether this task has been failed. */
    hasFailed(): boolean;
    /** Returns whether this task has an active rollback task going on. */
    isRollingBack(): boolean;
    /** Returns whether the rollback action was successful. */
    hasRolledBack(): boolean;
    /** Returns whether this task has an actively retrying task going on. */
    isRetrying(): boolean;
    /** Returns whether enabled function resolves to true. */
    isEnabled(): boolean;
    /** Returns whether this task actually has a title. */
    hasTitle(): boolean;
    /** Returns whether this task has a prompt inside. */
    isPrompt(): boolean;
    /** Run the current task. */
    run(context: Ctx, wrapper: TaskWrapper<Ctx, Renderer>): Promise<void>;
}
