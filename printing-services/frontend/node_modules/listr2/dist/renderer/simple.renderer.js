"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SimpleRenderer = void 0;
const log_update_1 = require("log-update");
const os_1 = require("os");
const event_constants_1 = require("../constants/event.constants");
const colorette_1 = require("../utils/colorette");
const figures_1 = require("../utils/figures");
/**
 * This is the default renderer which is neither verbose or updating.
 * It provides short output like update renderer, but does not disturb
 * stdin during execution of listr tasks
 */
class SimpleRenderer {
    constructor(tasks, options) {
        this.tasks = tasks;
        this.options = options;
        /**
         * Event type renderer map contains functions to process different task events
         */
        this.eventTypeRendererMap = {
            [event_constants_1.ListrEventType.SUBTASK]: (task) => {
                if (task.hasTitle()) {
                    // if Task has subtasks where we want to log the group indication
                    this.log(`${colorette_1.default.blue(figures_1.figures.pointer)} ${task.title}`);
                }
                if (task.hasSubtasks()) {
                    this.render(task.subtasks);
                }
            },
            [event_constants_1.ListrEventType.STATE]: (task) => {
                if (task.isCompleted() && task.hasTitle()) {
                    // The title is only logged at the end of the task execution
                    this.log(`${colorette_1.default.green(figures_1.figures.tick)} ${task.title}`);
                }
            },
            [event_constants_1.ListrEventType.DATA]: (task, event) => {
                // ! This is where it gets dirty
                // * We want the prompt to stay visible after confirmation
                if (task.isPrompt() && !String(event.data).match(/^\n$/)) {
                    (0, log_update_1.stderr)(`${event.data}`);
                }
                else {
                    this.log(`${figures_1.figures.pointerSmall} ${event.data}`);
                }
            },
            [event_constants_1.ListrEventType.MESSAGE]: (task, event) => {
                if (event.data.error) {
                    // error message
                    const title = SimpleRenderer.formatTitle(task);
                    this.log(`${colorette_1.default.red(figures_1.figures.cross)}${title}: ${event.data.error}`);
                }
                else if (event.data.skip) {
                    // Skip message
                    const title = SimpleRenderer.formatTitle(task);
                    const skip = task.title !== event.data.skip ? `: ${event.data.skip}` : '';
                    this.log(`${colorette_1.default.yellow(figures_1.figures.arrowDown)}${title} [${colorette_1.default.yellow(`skipped${skip}`)}]`);
                }
                else if (event.data.rollback) {
                    // rollback message
                    const title = SimpleRenderer.formatTitle(task);
                    this.log(`${colorette_1.default.red(figures_1.figures.arrowLeft)}${title}: ${event.data.rollback}`);
                }
                else if (event.data.retry) {
                    // Retry Message
                    const title = SimpleRenderer.formatTitle(task);
                    this.log(`[${colorette_1.default.yellow(`${event.data.retry.count}`)}]${title}`);
                }
            }
            // * We do not log out initial title. Only the final one.
            // [ListrEventType.TITLE]: (t, e) => this.renderTitle(t, e),
        };
        this.options = { ...SimpleRenderer.rendererOptions, ...options };
    }
    // This is used for mocks, since mocking Date is cumbesome
    static now() {
        return new Date();
    }
    // Used to sanitize title output
    static formatTitle(task) {
        return (task === null || task === void 0 ? void 0 : task.title) ? ` ${task.title}` : '';
    }
    // Writes sanitized output
    log(output) {
        const logOut = (msg) => {
            // Need appent \n to mimic console.log
            process[this.options.output].write(msg.endsWith(os_1.EOL) ? msg : `${msg}${os_1.EOL}`);
        };
        if (!this.options.prefixWithTimestamp) {
            logOut(`${output}`);
            return;
        }
        const now = SimpleRenderer.now();
        const timestamp = String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0') + ':' + String(now.getSeconds()).padStart(2, '0');
        logOut(`${colorette_1.default.dim(`[${timestamp}]`)} ${output}`);
    }
    // eslint-disable-next-line
    end() { }
    // yes this is a misuse :)
    render(tasks) {
        if (tasks === null || tasks === void 0 ? void 0 : tasks.length) {
            tasks.forEach((task) => {
                task.subscribe((event) => {
                    var _a, _b;
                    // Here event type will match event.type anyway
                    (_b = (_a = this.eventTypeRendererMap)[event.type]) === null || _b === void 0 ? void 0 : _b.call(_a, task, event);
                }, this.log);
            });
        }
        else {
            this.render(this.tasks);
        }
    }
}
exports.SimpleRenderer = SimpleRenderer;
// Designate this renderer as tty or nonTTY
SimpleRenderer.nonTTY = true;
// designate your renderer options that will be showed inside the `ListrOptions` as rendererOptions
SimpleRenderer.rendererOptions = { prefixWithTimestamp: false, output: 'stdout' };
