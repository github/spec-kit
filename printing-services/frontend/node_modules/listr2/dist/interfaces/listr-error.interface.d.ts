import { ListrRendererFactory } from './renderer.interface';
import { Task } from '../lib/task';
/** The internal error handling mechanism.. */
export declare class ListrError<Ctx extends Record<PropertyKey, any> = Record<PropertyKey, any>> extends Error {
    error: Error;
    type?: ListrErrorTypes;
    ctx?: Ctx;
    task?: Task<Ctx, ListrRendererFactory>;
    constructor(error: Error, type?: ListrErrorTypes, ctx?: Ctx, task?: Task<Ctx, ListrRendererFactory>);
}
/**
 * The actual error type that is collected and to help identify where the error is triggered from.
 */
export declare enum ListrErrorTypes {
    /** Task has failed and will try to retry. */
    WILL_RETRY = "WILL_RETRY",
    /** Task has failed and will try to rollback. */
    WILL_ROLLBACK = "WILL_ROLLBACK",
    /** Task has failed, ran the rollback action but the rollback action itself has failed. */
    HAS_FAILED_TO_ROLLBACK = "HAS_FAILED_TO_ROLLBACK",
    /** Task has failed. */
    HAS_FAILED = "HAS_FAILED",
    /** Task has failed, but exitOnError is set to false, so will ignore this error. */
    HAS_FAILED_WITHOUT_ERROR = "HAS_FAILED_WITHOUT_ERROR"
}
/** The internal error handling mechanism for prompts only. */
export declare class PromptError extends Error {
    constructor(message: string);
}
