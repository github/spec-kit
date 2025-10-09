/// <reference types="node" />
import type * as Enquirer from 'enquirer';
import type { Observable } from 'rxjs';
import { Readable } from 'stream';
import { ListrDefaultNonTTYRendererOptions, ListrDefaultRendererOptions, ListrDefaultRendererValue, ListrFallbackRendererValue, ListrGetRendererTaskOptions, ListrRendererFactory, ListrRendererValue } from './renderer.interface';
import { ListrEventType } from '../constants/event.constants';
import { Task } from '../lib/task';
import { TaskWrapper } from '../lib/task-wrapper';
import { Listr } from '../listr';
/** Listr Default Context */
export declare type ListrContext = any | undefined;
/**
 * ListrTask.
 *
 * Defines the task, conditions and options to run a specific task in the listr.
 */
export interface ListrTask<Ctx = ListrContext, Renderer extends ListrRendererFactory = any> {
    /**
     * Title of the task.
     *
     * Give this task a title if you want to track it by name in the current renderer.
     *
     * Tasks without a title will hide in the default renderer and are useful for running a background instance.
     * On verbose renderer, state changes from these tasks will log as 'Task without a title.'
     */
    title?: string;
    /**
     * The task itself.
     *
     * Task can be a sync or async function, an Observable, or a Stream.
     * Task will be executed, if the certain criteria of the state are met and whenever the time for that specific task has come.
     */
    task: (ctx: Ctx, task: TaskWrapper<Ctx, Renderer>) => void | ListrTaskResult<Ctx>;
    /**
     * Skip this task depending on the context.
     *
     * The function that has been passed in will be evaluated at the runtime when the task tries to initially run.
     */
    skip?: boolean | string | ((ctx: Ctx) => boolean | string | Promise<boolean | string>);
    /**
     * Enable a task depending on the context.
     *
     * The function that has been passed in will be evaluated at the initial creation of the Listr class for rendering purposes,
     * as well as re-evaluated when the time for that specific task has come.
     */
    enabled?: boolean | ((ctx: Ctx) => boolean | Promise<boolean>);
    /**
     * Adds the given number of retry attempts to the task if the task fails.
     */
    retry?: number;
    /**
     * Runs a specific event if the current task or any of the subtasks has failed.
     *
     * Mostly useful for rollback purposes for subtasks.
     * But can also be useful whenever a task is failed and some measures have to be taken to ensure the state is not changed.
     */
    rollback?: (ctx: Ctx, task: TaskWrapper<Ctx, Renderer>) => void | ListrTaskResult<Ctx>;
    /**
     * Set exit on the error option from task-level instead of setting it for all the subtasks.
     */
    exitOnError?: boolean | ((ctx: Ctx) => boolean | Promise<boolean>);
    /**
     * Per task options, that depends on the selected renderer.
     *
     * These options depend on the implementation of the selected renderer. If the selected renderer has no options it will
     * be displayed as never.
     */
    options?: ListrGetRendererTaskOptions<Renderer>;
}
/**
 * Options to set the behavior of this base task.
 */
export interface ListrOptions<Ctx = ListrContext> {
    /**
     * To inject a context through this options wrapper. Context can also be defined in run time.
     *
     * @default {}
     */
    ctx?: Ctx;
    /**
     * Concurrency sets how many tasks will be run at the same time in parallel.
     *
     * @default false > Default is to run everything synchronously.
     *
     * `true` will set it to `Infinity`, `false` will set it to synchronous.
     *
     * If you pass in a `number` it will limit it to that number.
     */
    concurrent?: boolean | number;
    /**
     * Determine the default behavior of exiting on errors.
     *
     * @default true > exit on any error coming from the tasks.
     */
    exitOnError?: boolean;
    /**
     * Determine the behavior of exiting after rollback actions.
     *
     * This is independent of exitOnError, since failure of a rollback can be a more critical operation comparing to
     * failing a single task.
     *
     * @default true > exit after rolling back tasks
     */
    exitAfterRollback?: boolean;
    /**
     * By default, Listr2 will track SIGINIT signal to update the renderer one last time before completely failing.
     *
     * @default true
     */
    registerSignalListeners?: boolean;
    /**
     * Determine the certain condition required to use the non-TTY renderer.
     *
     * @default null > handled internally
     */
    rendererFallback?: boolean | (() => boolean);
    /**
     * Determine the certain condition required to use the silent renderer.
     *
     * @default null > handled internally
     */
    rendererSilent?: boolean | (() => boolean);
    /**
     * Disabling the color, useful for tests and such.
     *
     * @default false
     */
    disableColor?: boolean;
    /**
     * Inject data directly to TaskWrapper.
     */
    injectWrapper?: {
        enquirer?: Enquirer<object>;
    };
}
/**
 * Task can be set of sync or async function, an Observable or a stream.
 */
export declare type ListrTaskResult<Ctx> = string | Promise<any> | Listr<Ctx, ListrRendererValue, any> | Readable | NodeJS.ReadableStream | Observable<any>;
/**
 * Parent class options.
 *
 * Parent class has more options where you can also select the and set renderer and non-tty renderer.
 *
 * Any subtasks will respect those options so they will be stripped of that properties.
 */
export declare type ListrBaseClassOptions<Ctx = ListrContext, Renderer extends ListrRendererValue = ListrDefaultRendererValue, FallbackRenderer extends ListrRendererValue = ListrFallbackRendererValue> = ListrOptions<Ctx> & ListrDefaultRendererOptions<Renderer> & ListrDefaultNonTTYRendererOptions<FallbackRenderer>;
/**
 * Sub class options.
 *
 * Subtasks has reduced set options where the missing ones are explicitly set by the base class.
 */
export declare type ListrSubClassOptions<Ctx = ListrContext, Renderer extends ListrRendererValue = ListrDefaultRendererValue> = ListrOptions<Ctx> & Omit<ListrDefaultRendererOptions<Renderer>, 'renderer'>;
/** The internal communication event. */
export declare type ListrEvent = {
    type: Exclude<ListrEventType, 'MESSAGE' | 'DATA'>;
    data?: string | boolean;
} | {
    type: ListrEventType.DATA;
    data: string;
} | {
    type: ListrEventType.MESSAGE;
    data: Task<any, any>['message'];
};
/**
 * Used to match event.type to ListrEvent permutations
 */
export declare type ListrEventFromType<T extends ListrEventType, E = ListrEvent> = E extends {
    type: infer U;
} ? T extends U ? E : never : never;
