"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Listr = void 0;
const pMap = require("p-map");
const rxjs_1 = require("rxjs");
const state_constants_1 = require("./constants/state.constants");
const task_1 = require("./lib/task");
const task_wrapper_1 = require("./lib/task-wrapper");
const renderer_1 = require("./utils/renderer");
/**
 * Creates a new set of Listr2 task list.
 */
class Listr {
    constructor(task, options) {
        var _a, _b, _c;
        this.task = task;
        this.options = options;
        this.tasks = [];
        this.err = [];
        this.renderHook$ = new rxjs_1.Subject();
        // assign over default options
        this.options = {
            ...{
                concurrent: false,
                renderer: 'default',
                nonTTYRenderer: 'verbose',
                exitOnError: true,
                exitAfterRollback: true,
                registerSignalListeners: true
            },
            ...options
        };
        // define parallel options
        if (this.options.concurrent === true) {
            this.concurrency = Infinity;
        }
        else if (typeof this.options.concurrent === 'number') {
            this.concurrency = this.options.concurrent;
        }
        else {
            this.concurrency = 1;
        }
        // get renderer class
        const renderer = (0, renderer_1.getRenderer)(this.options.renderer, this.options.nonTTYRenderer, (_a = this.options) === null || _a === void 0 ? void 0 : _a.rendererFallback, (_b = this.options) === null || _b === void 0 ? void 0 : _b.rendererSilent);
        this.rendererClass = renderer.renderer;
        // depending on the result pass the given options in
        if (!renderer.nonTTY) {
            this.rendererClassOptions = this.options.rendererOptions;
        }
        else {
            this.rendererClassOptions = this.options.nonTTYRendererOptions;
        }
        // parse and add tasks
        /* istanbul ignore next */
        this.add(task !== null && task !== void 0 ? task : []);
        // Graceful interrupt for render cleanup
        /* istanbul ignore if */
        if (this.options.registerSignalListeners) {
            process
                .once('SIGINT', () => {
                this.tasks.forEach(async (task) => {
                    if (task.isPending()) {
                        task.state$ = state_constants_1.ListrTaskState.FAILED;
                    }
                });
                this.renderer.end(new Error('Interrupted.'));
                process.exit(127);
            })
                .setMaxListeners(0);
        }
        // disable color programatically for CI purposes
        /* istanbul ignore if */
        if ((_c = this.options) === null || _c === void 0 ? void 0 : _c.disableColor) {
            process.env.LISTR_DISABLE_COLOR = '1';
        }
    }
    add(task) {
        const tasks = Array.isArray(task) ? task : [task];
        tasks.forEach((task) => {
            this.tasks.push(new task_1.Task(this, task, this.options, { ...this.rendererClassOptions, ...task.options }));
        });
    }
    async run(context) {
        var _a, _b, _c;
        // start the renderer
        if (!this.renderer) {
            this.renderer = new this.rendererClass(this.tasks, this.rendererClassOptions, this.renderHook$);
        }
        this.renderer.render();
        // create a new context
        this.ctx = (_c = (_b = (_a = this.options) === null || _a === void 0 ? void 0 : _a.ctx) !== null && _b !== void 0 ? _b : context) !== null && _c !== void 0 ? _c : {};
        // check if the items are enabled
        await this.checkAll(this.ctx);
        // run tasks
        try {
            await pMap(this.tasks, async (task) => {
                // check this item is enabled, conditions may change depending on context
                await task.check(this.ctx);
                return this.runTask(task, this.ctx, this.err);
            }, { concurrency: this.concurrency });
            this.renderer.end();
        }
        catch (err) {
            if (this.options.exitOnError !== false) {
                this.renderer.end(err);
                // Do not exit when explicitly set to `false`
                throw err;
            }
        }
        return this.ctx;
    }
    checkAll(context) {
        return Promise.all(this.tasks.map((task) => task.check(context)));
    }
    runTask(task, context, errors) {
        if (!task.isEnabled()) {
            return Promise.resolve();
        }
        return new task_wrapper_1.TaskWrapper(task, errors, this.options).run(context);
    }
}
exports.Listr = Listr;
