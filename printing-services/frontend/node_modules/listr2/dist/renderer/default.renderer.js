"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DefaultRenderer = void 0;
const cliTruncate = require("cli-truncate");
const logUpdate = require("log-update");
const os_1 = require("os");
const cliWrap = require("wrap-ansi");
const colorette_1 = require("../utils/colorette");
const figures_1 = require("../utils/figures");
const indent_string_1 = require("../utils/indent-string");
const is_unicode_supported_1 = require("../utils/is-unicode-supported");
const parse_time_1 = require("../utils/parse-time");
/** Default updating renderer for Listr2 */
class DefaultRenderer {
    constructor(tasks, options, renderHook$) {
        this.tasks = tasks;
        this.options = options;
        this.renderHook$ = renderHook$;
        this.bottomBar = {};
        this.spinner = !(0, is_unicode_supported_1.isUnicodeSupported)() ? ['-', '\\', '|', '/'] : ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
        this.spinnerPosition = 0;
        this.options = { ...DefaultRenderer.rendererOptions, ...this.options };
    }
    getTaskOptions(task) {
        return { ...DefaultRenderer.rendererTaskOptions, ...task.rendererTaskOptions };
    }
    isBottomBar(task) {
        const bottomBar = this.getTaskOptions(task).bottomBar;
        return typeof bottomBar === 'number' && bottomBar !== 0 || typeof bottomBar === 'boolean' && bottomBar !== false;
    }
    hasPersistentOutput(task) {
        return this.getTaskOptions(task).persistentOutput === true;
    }
    hasTimer(task) {
        return this.getTaskOptions(task).showTimer === true;
    }
    getSelfOrParentOption(task, key) {
        var _a, _b, _c;
        return (_b = (_a = task === null || task === void 0 ? void 0 : task.rendererOptions) === null || _a === void 0 ? void 0 : _a[key]) !== null && _b !== void 0 ? _b : (_c = this.options) === null || _c === void 0 ? void 0 : _c[key];
    }
    /* istanbul ignore next */
    getTaskTime(task) {
        return colorette_1.default.dim(`[${(0, parse_time_1.parseTaskTime)(task.message.duration)}]`);
    }
    createRender(options) {
        options = {
            ...{
                tasks: true,
                bottomBar: true,
                prompt: true
            },
            ...options
        };
        const render = [];
        const renderTasks = this.multiLineRenderer(this.tasks);
        const renderBottomBar = this.renderBottomBar();
        const renderPrompt = this.renderPrompt();
        if (options.tasks && (renderTasks === null || renderTasks === void 0 ? void 0 : renderTasks.trim().length) > 0) {
            render.push(renderTasks);
        }
        if (options.bottomBar && (renderBottomBar === null || renderBottomBar === void 0 ? void 0 : renderBottomBar.trim().length) > 0) {
            render.push((render.length > 0 ? os_1.EOL : '') + renderBottomBar);
        }
        if (options.prompt && (renderPrompt === null || renderPrompt === void 0 ? void 0 : renderPrompt.trim().length) > 0) {
            render.push((render.length > 0 ? os_1.EOL : '') + renderPrompt);
        }
        return render.length > 0 ? render.join(os_1.EOL) : '';
    }
    render() {
        var _a;
        // Do not render if we are already rendering
        if (this.id) {
            return;
        }
        const updateRender = () => logUpdate(this.createRender());
        /* istanbul ignore if */
        if (!((_a = this.options) === null || _a === void 0 ? void 0 : _a.lazy)) {
            this.id = setInterval(() => {
                this.spinnerPosition = ++this.spinnerPosition % this.spinner.length;
                updateRender();
            }, 100);
        }
        this.renderHook$.subscribe(() => {
            updateRender();
        });
    }
    end() {
        clearInterval(this.id);
        if (this.id) {
            this.id = undefined;
        }
        // clear log updater
        logUpdate.clear();
        logUpdate.done();
        // directly write to process.stdout, since logupdate only can update the seen height of terminal
        if (!this.options.clearOutput) {
            process.stdout.write(this.createRender({ prompt: false }) + os_1.EOL);
        }
    }
    // eslint-disable-next-line
    multiLineRenderer(tasks, level = 0) {
        var _a, _b;
        let output = [];
        for (const task of tasks) {
            if (task.isEnabled()) {
                // Current Task Title
                if (task.hasTitle()) {
                    if (!(tasks.some((task) => task.hasFailed()) && !task.hasFailed() && task.options.exitOnError !== false && !(task.isCompleted() || task.isSkipped()))) {
                        // if task is skipped
                        if (task.hasFailed() && this.getSelfOrParentOption(task, 'collapseErrors')) {
                            // current task title and skip change the title
                            output = [
                                ...output,
                                this.formatString(!task.hasSubtasks() && task.message.error && this.getSelfOrParentOption(task, 'showErrorMessage') ? task.message.error : task.title, this.getSymbol(task), level)
                            ];
                        }
                        else if (task.isSkipped() && this.getSelfOrParentOption(task, 'collapseSkips')) {
                            // current task title and skip change the title
                            output = [
                                ...output,
                                this.formatString(this.addSuffixToMessage(task.message.skip && this.getSelfOrParentOption(task, 'showSkipMessage') ? task.message.skip : task.title, 'SKIPPED', this.getSelfOrParentOption(task, 'suffixSkips')), this.getSymbol(task), level)
                            ];
                        }
                        else if (task.isRetrying() && this.getSelfOrParentOption(task, 'suffixRetries')) {
                            output = [...output, this.formatString(this.addSuffixToMessage(task.title, `RETRYING-${task.message.retry.count}`), this.getSymbol(task), level)];
                        }
                        else if (task.isCompleted() && task.hasTitle() && (this.getSelfOrParentOption(task, 'showTimer') || this.hasTimer(task))) {
                            // task with timer
                            output = [...output, this.formatString(`${task === null || task === void 0 ? void 0 : task.title} ${this.getTaskTime(task)}`, this.getSymbol(task), level)];
                        }
                        else {
                            // normal state
                            output = [...output, this.formatString(task.title, this.getSymbol(task), level)];
                        }
                    }
                    else {
                        // some sibling task but self has failed and this has stopped
                        output = [...output, this.formatString(task.title, colorette_1.default.red(figures_1.figures.squareSmallFilled), level)];
                    }
                }
                // task should not have subtasks since subtasks will handle the error already
                // maybe it is a better idea to show the error or skip messages when show subtasks is disabled.
                if (!task.hasSubtasks() || !this.getSelfOrParentOption(task, 'showSubtasks')) {
                    // without the collapse option for skip and errors
                    if (task.hasFailed() &&
                        this.getSelfOrParentOption(task, 'collapseErrors') === false &&
                        (this.getSelfOrParentOption(task, 'showErrorMessage') || !this.getSelfOrParentOption(task, 'showSubtasks'))) {
                        // show skip data if collapsing is not defined
                        output = [...output, this.dumpData(task, level, 'error')];
                    }
                    else if (task.isSkipped() &&
                        this.getSelfOrParentOption(task, 'collapseSkips') === false &&
                        (this.getSelfOrParentOption(task, 'showSkipMessage') || !this.getSelfOrParentOption(task, 'showSubtasks'))) {
                        // show skip data if collapsing is not defined
                        output = [...output, this.dumpData(task, level, 'skip')];
                    }
                }
                // Current Task Output
                if (task === null || task === void 0 ? void 0 : task.output) {
                    if ((task.isPending() || task.isRetrying() || task.isRollingBack()) && task.isPrompt()) {
                        // data output to prompt bar if prompt
                        this.promptBar = task.output;
                    }
                    else if (this.isBottomBar(task) || !task.hasTitle()) {
                        // data output to bottom bar
                        const data = [this.dumpData(task, -1)];
                        // create new if there is no persistent storage created for bottom bar
                        if (!this.bottomBar[task.id]) {
                            this.bottomBar[task.id] = {};
                            this.bottomBar[task.id].data = [];
                            const bottomBar = this.getTaskOptions(task).bottomBar;
                            if (typeof bottomBar === 'boolean') {
                                this.bottomBar[task.id].items = 1;
                            }
                            else {
                                this.bottomBar[task.id].items = bottomBar;
                            }
                        }
                        // persistent bottom bar and limit items in it
                        if (!((_b = (_a = this.bottomBar[task.id]) === null || _a === void 0 ? void 0 : _a.data) === null || _b === void 0 ? void 0 : _b.some((element) => data.includes(element))) && !task.isSkipped()) {
                            this.bottomBar[task.id].data = [...this.bottomBar[task.id].data, ...data];
                        }
                    }
                    else if (task.isPending() || task.isRetrying() || task.isRollingBack() || this.hasPersistentOutput(task)) {
                        // keep output if persistent output is set
                        output = [...output, this.dumpData(task, level)];
                    }
                }
                // render subtasks, some complicated conditionals going on
                if (
                // check if renderer option is on first
                this.getSelfOrParentOption(task, 'showSubtasks') !== false &&
                    // if it doesnt have subtasks no need to check
                    task.hasSubtasks() &&
                    (task.isPending() ||
                        task.hasFailed() ||
                        task.isCompleted() && !task.hasTitle() ||
                        // have to be completed and have subtasks
                        task.isCompleted() && this.getSelfOrParentOption(task, 'collapse') === false && !task.subtasks.some((subtask) => subtask.rendererOptions.collapse === true) ||
                        // if any of the subtasks have the collapse option of
                        task.subtasks.some((subtask) => subtask.rendererOptions.collapse === false) ||
                        // if any of the subtasks has failed
                        task.subtasks.some((subtask) => subtask.hasFailed()) ||
                        // if any of the subtasks rolled back
                        task.subtasks.some((subtask) => subtask.hasRolledBack()))) {
                    // set level
                    const subtaskLevel = !task.hasTitle() ? level : level + 1;
                    // render the subtasks as in the same way
                    const subtaskRender = this.multiLineRenderer(task.subtasks, subtaskLevel);
                    if ((subtaskRender === null || subtaskRender === void 0 ? void 0 : subtaskRender.trim()) !== '' && !task.subtasks.every((subtask) => !subtask.hasTitle())) {
                        output = [...output, subtaskRender];
                    }
                }
                // after task is finished actions
                if (task.isCompleted() || task.hasFailed() || task.isSkipped() || task.hasRolledBack()) {
                    // clean up prompts
                    this.promptBar = null;
                    // clean up bottom bar items if not indicated otherwise
                    if (!this.hasPersistentOutput(task)) {
                        delete this.bottomBar[task.id];
                    }
                }
            }
        }
        output = output.filter(Boolean);
        if (output.length > 0) {
            return output.join(os_1.EOL);
        }
        else {
            return;
        }
    }
    renderBottomBar() {
        // parse through all objects return only the last mentioned items
        if (Object.keys(this.bottomBar).length > 0) {
            this.bottomBar = Object.keys(this.bottomBar).reduce((o, key) => {
                if (!(o === null || o === void 0 ? void 0 : o[key])) {
                    o[key] = {};
                }
                o[key] = this.bottomBar[key];
                this.bottomBar[key].data = this.bottomBar[key].data.slice(-this.bottomBar[key].items);
                o[key].data = this.bottomBar[key].data;
                return o;
            }, {});
            return Object.values(this.bottomBar)
                .reduce((o, value) => o = [...o, ...value.data], [])
                .filter(Boolean)
                .join(os_1.EOL);
        }
    }
    renderPrompt() {
        if (this.promptBar) {
            return this.promptBar;
        }
    }
    dumpData(task, level, source = 'output') {
        let data;
        switch (source) {
            case 'output':
                data = task.output;
                break;
            case 'skip':
                data = task.message.skip;
                break;
            case 'error':
                data = task.message.error;
                break;
        }
        // dont return anything on some occasions
        if (task.hasTitle() && source === 'error' && data === task.title) {
            return;
        }
        if (typeof data === 'string') {
            return this.formatString(data, this.getSymbol(task, true), level + 1);
        }
    }
    formatString(str, icon, level) {
        // we dont like empty data around here
        if (str.trim() === '') {
            return;
        }
        str = `${icon} ${str}`;
        let parsedStr;
        let columns = process.stdout.columns ? process.stdout.columns : 80;
        columns = columns - level * this.options.indentation - 2;
        switch (this.options.formatOutput) {
            case 'truncate':
                parsedStr = str.split(os_1.EOL).map((s, i) => {
                    return cliTruncate(this.indentMultilineOutput(s, i), columns);
                });
                break;
            case 'wrap':
                parsedStr = cliWrap(str, columns, { hard: true })
                    .split(os_1.EOL)
                    .map((s, i) => this.indentMultilineOutput(s, i));
                break;
            default:
                throw new Error('Format option for the renderer is wrong.');
        }
        // this removes the empty lines
        if (this.options.removeEmptyLines) {
            parsedStr = parsedStr.filter(Boolean);
        }
        return (0, indent_string_1.indentString)(parsedStr.join(os_1.EOL), level * this.options.indentation);
    }
    indentMultilineOutput(str, i) {
        return i > 0 ? (0, indent_string_1.indentString)(str.trim(), 2) : str.trim();
    }
    // eslint-disable-next-line complexity
    getSymbol(task, data = false) {
        var _a, _b, _c;
        if (task.isPending() && !data) {
            return ((_a = this.options) === null || _a === void 0 ? void 0 : _a.lazy) || this.getSelfOrParentOption(task, 'showSubtasks') !== false && task.hasSubtasks() && !task.subtasks.every((subtask) => !subtask.hasTitle())
                ? colorette_1.default.yellow(figures_1.figures.pointer)
                : colorette_1.default.yellowBright(this.spinner[this.spinnerPosition]);
        }
        else if (task.isCompleted() && !data) {
            return task.hasSubtasks() && task.subtasks.some((subtask) => subtask.hasFailed()) ? colorette_1.default.yellow(figures_1.figures.warning) : colorette_1.default.green(figures_1.figures.tick);
        }
        else if (task.isRetrying() && !data) {
            return ((_b = this.options) === null || _b === void 0 ? void 0 : _b.lazy) ? colorette_1.default.yellow(figures_1.figures.warning) : colorette_1.default.yellow(this.spinner[this.spinnerPosition]);
        }
        else if (task.isRollingBack() && !data) {
            return ((_c = this.options) === null || _c === void 0 ? void 0 : _c.lazy) ? colorette_1.default.red(figures_1.figures.warning) : colorette_1.default.red(this.spinner[this.spinnerPosition]);
        }
        else if (task.hasRolledBack() && !data) {
            return colorette_1.default.red(figures_1.figures.arrowLeft);
        }
        else if (task.hasFailed() && !data) {
            return task.hasSubtasks() ? colorette_1.default.red(figures_1.figures.pointer) : colorette_1.default.red(figures_1.figures.cross);
        }
        else if (task.isSkipped() && !data && this.getSelfOrParentOption(task, 'collapseSkips') === false) {
            return colorette_1.default.yellow(figures_1.figures.warning);
        }
        else if (task.isSkipped() && (data || this.getSelfOrParentOption(task, 'collapseSkips'))) {
            return colorette_1.default.yellow(figures_1.figures.arrowDown);
        }
        return !data ? colorette_1.default.dim(figures_1.figures.squareSmallFilled) : figures_1.figures.pointerSmall;
    }
    addSuffixToMessage(message, suffix, condition) {
        return (condition !== null && condition !== void 0 ? condition : true) ? message + colorette_1.default.dim(` [${suffix}]`) : message;
    }
}
exports.DefaultRenderer = DefaultRenderer;
/** designates whether this renderer can output to a non-tty console */
DefaultRenderer.nonTTY = false;
/** renderer options for the defauult renderer */
DefaultRenderer.rendererOptions = {
    indentation: 2,
    clearOutput: false,
    showSubtasks: true,
    collapse: true,
    collapseSkips: true,
    showSkipMessage: true,
    suffixSkips: true,
    collapseErrors: true,
    showErrorMessage: true,
    suffixRetries: true,
    lazy: false,
    showTimer: false,
    removeEmptyLines: true,
    formatOutput: 'truncate'
};
