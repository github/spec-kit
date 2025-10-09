"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
// Vendored from @cypress/listr-verbose-renderer
const figures_1 = __importDefault(require("figures"));
const cli_cursor_1 = __importDefault(require("cli-cursor"));
const chalk_1 = __importDefault(require("chalk"));
const dayjs_1 = __importDefault(require("dayjs"));
const formattedLog = (options, output) => {
    const timestamp = (0, dayjs_1.default)().format(options.dateFormat);
    // eslint-disable-next-line no-console
    console.log(`${chalk_1.default.dim(`[${timestamp}]`)} ${output}`);
};
const renderHelper = (task, event, options) => {
    const log = formattedLog.bind(undefined, options);
    if (event.type === 'STATE') {
        const message = task.isPending() ? 'started' : task.state;
        log(`${task.title} [${message}]`);
        if (task.isSkipped() && task.output) {
            log(`${figures_1.default.arrowRight} ${task.output}`);
        }
    }
    else if (event.type === 'TITLE') {
        log(`${task.title} [title changed]`);
    }
};
const render = (tasks, options) => {
    for (const task of tasks) {
        task.subscribe((event) => {
            if (event.type === 'SUBTASKS') {
                render(task.subtasks, options);
                return;
            }
            renderHelper(task, event, options);
        }, (err) => {
            // eslint-disable-next-line no-console
            console.log(err);
        });
    }
};
class VerboseRenderer {
    constructor(tasks, options) {
        this._tasks = tasks;
        this._options = Object.assign({
            dateFormat: 'HH:mm:ss',
        }, options);
    }
    static get nonTTY() {
        return true;
    }
    render() {
        cli_cursor_1.default.hide();
        render(this._tasks, this._options);
    }
    end() {
        cli_cursor_1.default.show();
    }
}
exports.default = VerboseRenderer;
