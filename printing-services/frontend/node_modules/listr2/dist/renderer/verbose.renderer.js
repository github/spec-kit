"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.VerboseRenderer = void 0;
const event_constants_1 = require("../constants/event.constants");
const logger_1 = require("../utils/logger");
const parse_time_1 = require("../utils/parse-time");
class VerboseRenderer {
    constructor(tasks, options) {
        var _a, _b, _c, _d;
        this.tasks = tasks;
        this.options = options;
        if (((_a = this.options) === null || _a === void 0 ? void 0 : _a.logger) && ((_b = this.options) === null || _b === void 0 ? void 0 : _b.options)) {
            this.logger = new this.options.logger(this.options.options);
        }
        else if ((_c = this.options) === null || _c === void 0 ? void 0 : _c.logger) {
            this.logger = new this.options.logger();
        }
        else {
            this.logger = new logger_1.Logger({ useIcons: (_d = this.options) === null || _d === void 0 ? void 0 : _d.useIcons });
        }
        this.options = { ...VerboseRenderer.rendererOptions, ...this.options };
    }
    render() {
        this.verboseRenderer(this.tasks);
    }
    // eslint-disable-next-line @typescript-eslint/no-empty-function
    end() { }
    // verbose renderer multi-level
    verboseRenderer(tasks) {
        return tasks === null || tasks === void 0 ? void 0 : tasks.forEach((task) => {
            task.subscribe(
            // eslint-disable-next-line complexity
            (event) => {
                var _a, _b, _c, _d, _e, _f, _g, _h;
                if (task.isEnabled()) {
                    // render depending on the state
                    const taskTitle = task.hasTitle() ? task.title : 'Task without title.';
                    if (event.type === event_constants_1.ListrEventType.SUBTASK && task.hasSubtasks()) {
                        // render lower level if multi-level
                        this.verboseRenderer(task.subtasks);
                    }
                    else if (event.type === event_constants_1.ListrEventType.STATE) {
                        if (((_a = this.options) === null || _a === void 0 ? void 0 : _a.logEmptyTitle) !== false || task.hasTitle()) {
                            if (task.isPending()) {
                                this.logger.start(taskTitle);
                            }
                            else if (task.isCompleted()) {
                                this.logger.success(taskTitle + (((_b = this.options) === null || _b === void 0 ? void 0 : _b.showTimer) && ((_c = task.message) === null || _c === void 0 ? void 0 : _c.duration) ? ` [${(0, parse_time_1.parseTaskTime)(task.message.duration)}]` : ''));
                            }
                        }
                    }
                    else if (event.type === event_constants_1.ListrEventType.DATA && !!event.data) {
                        this.logger.data(String(event.data));
                    }
                    else if (event.type === event_constants_1.ListrEventType.TITLE) {
                        if (((_d = this.options) === null || _d === void 0 ? void 0 : _d.logTitleChange) !== false) {
                            this.logger.title(String(event.data));
                        }
                    }
                    else if (event.type === event_constants_1.ListrEventType.MESSAGE) {
                        if ((_e = event.data) === null || _e === void 0 ? void 0 : _e.error) {
                            // error message
                            this.logger.fail(String(event.data.error));
                        }
                        else if ((_f = event.data) === null || _f === void 0 ? void 0 : _f.skip) {
                            // skip message
                            this.logger.skip(String(event.data.skip));
                        }
                        else if ((_g = event.data) === null || _g === void 0 ? void 0 : _g.rollback) {
                            // rollback message
                            this.logger.rollback(String(event.data.rollback));
                        }
                        else if ((_h = event.data) === null || _h === void 0 ? void 0 : _h.retry) {
                            // inform of retry count
                            this.logger.retry(`[${event.data.retry.count}] ` + String(taskTitle));
                        }
                    }
                }
            }, 
            /* istanbul ignore next */ (err) => {
                this.logger.fail(err);
            });
        });
    }
}
exports.VerboseRenderer = VerboseRenderer;
/** designates whether this renderer can output to a non-tty console */
VerboseRenderer.nonTTY = true;
/** renderer options for the verbose renderer */
VerboseRenderer.rendererOptions = {
    useIcons: false,
    logEmptyTitle: true,
    logTitleChange: true
};
