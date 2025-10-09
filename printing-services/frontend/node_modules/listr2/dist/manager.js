"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Manager = void 0;
const listr_1 = require("./listr");
/**
 * Creates a new Listr2 task manager.
 *
 * Useful for creating a single instace of Listr2 with pre-set settings.
 */
class Manager {
    constructor(options) {
        this.options = options;
        this.err = [];
        this.tasks = [];
    }
    set ctx(ctx) {
        this.options.ctx = ctx;
    }
    add(tasks, options) {
        options = { ...this.options, ...options };
        this.tasks = [...this.tasks, this.indent(tasks, options)];
    }
    async runAll(options) {
        options = { ...this.options, ...options };
        const ctx = await this.run(this.tasks, options);
        // clear out queues
        this.tasks = [];
        return ctx;
    }
    newListr(tasks, options) {
        return new listr_1.Listr(tasks, options);
    }
    indent(tasks, options, taskOptions) {
        options = { ...this.options, ...options };
        let newTask;
        // type function or directly
        if (typeof tasks === 'function') {
            newTask = {
                ...taskOptions,
                task: (ctx) => this.newListr(tasks(ctx), options)
            };
        }
        else {
            newTask = {
                ...taskOptions,
                task: () => this.newListr(tasks, options)
            };
        }
        return newTask;
    }
    async run(tasks, options) {
        options = { ...this.options, ...options };
        // create task
        const task = this.newListr(tasks, options);
        // run task
        const ctx = await task.run();
        // reset error queue
        this.err = task.err;
        return ctx;
    }
    // general utils
    /* istanbul ignore next */
    getRuntime(pipetime) {
        return `${Math.round(Date.now() - pipetime) / 1000}s`;
    }
}
exports.Manager = Manager;
