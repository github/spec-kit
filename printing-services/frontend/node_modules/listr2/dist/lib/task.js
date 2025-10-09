"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Task = void 0;
const rxjs_1 = require("rxjs");
const stream_1 = require("stream");
const event_constants_1 = require("../constants/event.constants");
const state_constants_1 = require("../constants/state.constants");
const listr_error_interface_1 = require("../interfaces/listr-error.interface");
const listr_1 = require("../listr");
const assert_1 = require("../utils/assert");
const renderer_1 = require("../utils/renderer");
const uuid_1 = require("../utils/uuid");
/**
 * Create a task from the given set of variables and make it runnable.
 */
class Task extends rxjs_1.Subject {
    constructor(listr, tasks, options, rendererOptions) {
        var _a, _b, _c, _d, _e, _f;
        super();
        this.listr = listr;
        this.tasks = tasks;
        this.options = options;
        this.rendererOptions = rendererOptions;
        /**
         * A channel for messages.
         *
         * This requires a separate channel for messages like error, skip or runtime messages to further utilize in the renderers.
         */
        this.message = {};
        // this kind of randomness is enough for task ids
        this.id = (0, uuid_1.generateUUID)();
        this.title = (_a = this.tasks) === null || _a === void 0 ? void 0 : _a.title;
        this.initialTitle = (_b = this.tasks) === null || _b === void 0 ? void 0 : _b.title;
        this.task = this.tasks.task;
        // parse functions
        this.skip = (_d = (_c = this.tasks) === null || _c === void 0 ? void 0 : _c.skip) !== null && _d !== void 0 ? _d : false;
        this.enabledFn = (_f = (_e = this.tasks) === null || _e === void 0 ? void 0 : _e.enabled) !== null && _f !== void 0 ? _f : true;
        // task options
        this.rendererTaskOptions = this.tasks.options;
        this.renderHook$ = this.listr.renderHook$;
        this.subscribe(() => {
            this.renderHook$.next();
        });
    }
    set state$(state) {
        this.state = state;
        this.next({
            type: event_constants_1.ListrEventType.STATE,
            data: state
        });
        // cancel the subtasks if this has already failed
        if (this.hasSubtasks() && this.hasFailed()) {
            for (const subtask of this.subtasks) {
                if (subtask.state === state_constants_1.ListrTaskState.PENDING) {
                    subtask.state$ = state_constants_1.ListrTaskState.FAILED;
                }
            }
        }
    }
    set output$(data) {
        this.output = data;
        this.next({
            type: event_constants_1.ListrEventType.DATA,
            data
        });
    }
    set message$(data) {
        this.message = { ...this.message, ...data };
        this.next({
            type: event_constants_1.ListrEventType.MESSAGE,
            data
        });
    }
    set title$(title) {
        this.title = title;
        this.next({
            type: event_constants_1.ListrEventType.TITLE,
            data: title
        });
    }
    /**
     * A function to check whether this task should run at all via enable.
     */
    async check(ctx) {
        // Check if a task is enabled or disabled
        if (this.state === undefined) {
            this.enabled = await (0, assert_1.assertFunctionOrSelf)(this.enabledFn, ctx);
            this.next({
                type: event_constants_1.ListrEventType.ENABLED,
                data: this.enabled
            });
        }
    }
    /** Returns whether this task has subtasks. */
    hasSubtasks() {
        var _a;
        return ((_a = this.subtasks) === null || _a === void 0 ? void 0 : _a.length) > 0;
    }
    /** Returns whether this task is in progress. */
    isPending() {
        return this.state === state_constants_1.ListrTaskState.PENDING;
    }
    /** Returns whether this task is skipped. */
    isSkipped() {
        return this.state === state_constants_1.ListrTaskState.SKIPPED;
    }
    /** Returns whether this task has been completed. */
    isCompleted() {
        return this.state === state_constants_1.ListrTaskState.COMPLETED;
    }
    /** Returns whether this task has been failed. */
    hasFailed() {
        return this.state === state_constants_1.ListrTaskState.FAILED;
    }
    /** Returns whether this task has an active rollback task going on. */
    isRollingBack() {
        return this.state === state_constants_1.ListrTaskState.ROLLING_BACK;
    }
    /** Returns whether the rollback action was successful. */
    hasRolledBack() {
        return this.state === state_constants_1.ListrTaskState.ROLLED_BACK;
    }
    /** Returns whether this task has an actively retrying task going on. */
    isRetrying() {
        return this.state === state_constants_1.ListrTaskState.RETRY;
    }
    /** Returns whether enabled function resolves to true. */
    isEnabled() {
        return this.enabled;
    }
    /** Returns whether this task actually has a title. */
    hasTitle() {
        return typeof (this === null || this === void 0 ? void 0 : this.title) === 'string';
    }
    /** Returns whether this task has a prompt inside. */
    isPrompt() {
        return !!this.prompt;
    }
    /** Run the current task. */
    async run(context, wrapper) {
        var _a, _b, _c, _d, _e;
        const handleResult = (result) => {
            if (result instanceof listr_1.Listr) {
                // Detect the subtask
                // assign options
                result.options = { ...this.options, ...result.options };
                // switch to silent renderer since already rendering
                result.rendererClass = (0, renderer_1.getRenderer)('silent').renderer;
                result.renderHook$.subscribe(() => {
                    this.renderHook$.next();
                });
                // assign subtasks
                this.subtasks = result.tasks;
                result.err = this.listr.err;
                this.next({ type: event_constants_1.ListrEventType.SUBTASK });
                result = result.run(context);
            }
            else if (this.isPrompt()) {
                // do nothing, it is already being handled
            }
            else if (result instanceof Promise) {
                // Detect promise
                result = result.then(handleResult);
            }
            else if (result instanceof stream_1.Readable) {
                // Detect stream
                result = new Promise((resolve, reject) => {
                    result.on('data', (data) => {
                        this.output$ = data.toString();
                    });
                    result.on('error', (error) => reject(error));
                    result.on('end', () => resolve(null));
                });
            }
            else if (result instanceof rxjs_1.Observable) {
                // Detect Observable
                result = new Promise((resolve, reject) => {
                    result.subscribe({
                        next: (data) => {
                            this.output$ = data;
                        },
                        error: reject,
                        complete: resolve
                    });
                });
            }
            return result;
        };
        const startTime = Date.now();
        // finish the task first
        this.state$ = state_constants_1.ListrTaskState.PENDING;
        // check if this function wants to be skipped
        const skipped = await (0, assert_1.assertFunctionOrSelf)(this.skip, context);
        if (skipped) {
            if (typeof skipped === 'string') {
                this.message$ = { skip: skipped };
            }
            else if (this.hasTitle()) {
                this.message$ = { skip: this.title };
            }
            else {
                this.message$ = { skip: 'Skipped task without a title.' };
            }
            this.state$ = state_constants_1.ListrTaskState.SKIPPED;
            return;
        }
        try {
            // add retry functionality
            const retryCount = ((_a = this.tasks) === null || _a === void 0 ? void 0 : _a.retry) && ((_b = this.tasks) === null || _b === void 0 ? void 0 : _b.retry) > 0 ? this.tasks.retry + 1 : 1;
            for (let retries = 1; retries <= retryCount; retries++) {
                try {
                    // handle the results
                    await handleResult(this.task(context, wrapper));
                    break;
                }
                catch (err) {
                    if (retries !== retryCount) {
                        this.retry = { count: retries, withError: err };
                        this.message$ = { retry: this.retry };
                        this.title$ = this.initialTitle;
                        this.output = undefined;
                        wrapper.report(err, listr_error_interface_1.ListrErrorTypes.WILL_RETRY);
                        this.state$ = state_constants_1.ListrTaskState.RETRY;
                    }
                    else {
                        throw err;
                    }
                }
            }
            if (this.isPending() || this.isRetrying()) {
                this.message$ = { duration: Date.now() - startTime };
                this.state$ = state_constants_1.ListrTaskState.COMPLETED;
            }
        }
        catch (error) {
            // catch prompt error, this was the best i could do without going crazy
            if (this.prompt instanceof listr_error_interface_1.PromptError) {
                // eslint-disable-next-line no-ex-assign
                error = new Error(this.prompt.message);
            }
            // execute the task on error function
            if ((_c = this.tasks) === null || _c === void 0 ? void 0 : _c.rollback) {
                wrapper.report(error, listr_error_interface_1.ListrErrorTypes.WILL_ROLLBACK);
                try {
                    this.state$ = state_constants_1.ListrTaskState.ROLLING_BACK;
                    await this.tasks.rollback(context, wrapper);
                    this.state$ = state_constants_1.ListrTaskState.ROLLED_BACK;
                    this.message$ = { rollback: this.title };
                }
                catch (err) {
                    this.state$ = state_constants_1.ListrTaskState.FAILED;
                    wrapper.report(err, listr_error_interface_1.ListrErrorTypes.HAS_FAILED_TO_ROLLBACK);
                    throw err;
                }
                if (((_d = this.listr.options) === null || _d === void 0 ? void 0 : _d.exitAfterRollback) !== false) {
                    // Do not exit when explicitly set to `false`
                    throw new Error(this.title);
                }
            }
            else {
                // mark task as failed
                this.state$ = state_constants_1.ListrTaskState.FAILED;
                if (this.listr.options.exitOnError !== false && await (0, assert_1.assertFunctionOrSelf)((_e = this.tasks) === null || _e === void 0 ? void 0 : _e.exitOnError, context) !== false) {
                    // Do not exit when explicitly set to `false`
                    // report error
                    wrapper.report(error, listr_error_interface_1.ListrErrorTypes.HAS_FAILED);
                    throw error;
                }
                else if (!this.hasSubtasks()) {
                    // subtasks will handle and report their own errors
                    wrapper.report(error, listr_error_interface_1.ListrErrorTypes.HAS_FAILED_WITHOUT_ERROR);
                }
            }
        }
        finally {
            // Mark the observable as completed
            this.complete();
        }
    }
}
exports.Task = Task;
