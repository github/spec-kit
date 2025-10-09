"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TaskWrapper = void 0;
const through = require("through");
const clearline_regex_constants_1 = require("../constants/clearline-regex.constants");
const state_constants_1 = require("../constants/state.constants");
const listr_error_interface_1 = require("../interfaces/listr-error.interface");
const listr_1 = require("../listr");
const general_1 = require("../utils/general");
const prompt_1 = require("../utils/prompt");
/**
 * Extend the task to have more functionality while accesing from the outside.
 */
class TaskWrapper {
    constructor(task, errors, options) {
        this.task = task;
        this.errors = errors;
        this.options = options;
    }
    /** Change the title of the current task. */
    set title(data) {
        this.task.title$ = data;
    }
    /** Get the title of the current task. */
    get title() {
        return this.task.title;
    }
    /** Send a output to the output channel. */
    set output(data) {
        this.task.output$ = data;
    }
    /** Get the output from the output channel. */
    get output() {
        return this.task.output;
    }
    /** Create a new subtask with given renderer selection from the parent task. */
    newListr(task, options) {
        let tasks;
        if (typeof task === 'function') {
            tasks = task(this);
        }
        else {
            tasks = task;
        }
        return new listr_1.Listr(tasks, options);
    }
    /** Report a error in process for error collection. */
    report(error, type) {
        var _a, _b, _c;
        this.errors.push(new listr_error_interface_1.ListrError(error, type, (0, general_1.cloneObject)(this.task.listr.ctx), (0, general_1.cloneObject)(this.task)));
        this.task.message$ = { error: (_c = (_a = error.message) !== null && _a !== void 0 ? _a : (_b = this.task) === null || _b === void 0 ? void 0 : _b.title) !== null && _c !== void 0 ? _c : 'Task with no title.' };
    }
    /** Skip current task. */
    skip(message) {
        var _a, _b;
        this.task.state$ = state_constants_1.ListrTaskState.SKIPPED;
        if (message) {
            this.task.message$ = { skip: (_b = message !== null && message !== void 0 ? message : (_a = this.task) === null || _a === void 0 ? void 0 : _a.title) !== null && _b !== void 0 ? _b : 'Task with no title.' };
        }
    }
    /** Get the number of retrying, else returns false */
    isRetrying() {
        return this.task.isRetrying() ? this.task.retry : { count: 0 };
    }
    /**
     * Create a new Enquirer prompt using prompt options.
     *
     * Since process.stdout is controlled by Listr, this will passthrough all Enquirer data through internal stdout.
     */
    async prompt(options) {
        var _a;
        return prompt_1.createPrompt.bind(this)(options, { ...(_a = this.options) === null || _a === void 0 ? void 0 : _a.injectWrapper });
    }
    /** Cancels the current prompt attach to this task. */
    cancelPrompt(throwError = false) {
        return prompt_1.destroyPrompt.bind(this)(throwError);
    }
    /**
     * Pass stream of data to internal stdout.
     *
     * Since Listr2 takes control of process.stdout utilizing the default renderer, any data outputted to process.stdout
     * will corupt its looks.
     *
     * This returns a fake stream to pass any stream inside Listr as task data.
     */
    stdout() {
        return through((chunk) => {
            chunk = chunk.toString();
            chunk = chunk.replace(new RegExp(clearline_regex_constants_1.CLEAR_LINE_REGEX, 'gmi'), '');
            chunk = chunk.replace(new RegExp(clearline_regex_constants_1.BELL_REGEX, 'gmi'), '');
            if (chunk !== '') {
                this.output = chunk;
            }
        });
    }
    /** Run this task. */
    run(ctx) {
        return this.task.run(ctx, this);
    }
}
exports.TaskWrapper = TaskWrapper;
