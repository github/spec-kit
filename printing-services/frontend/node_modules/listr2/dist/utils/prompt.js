"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.destroyPrompt = exports.createPrompt = void 0;
const event_constants_1 = require("../constants/event.constants");
const state_constants_1 = require("../constants/state.constants");
const listr_error_interface_1 = require("../interfaces/listr-error.interface");
const task_wrapper_1 = require("../lib/task-wrapper");
/**
 * Create a new prompt with Enquirer externally.
 * This extends enquirer so you dont have to give a name to single prompts and such so it is also
 * useful to use externally.
 * @param this
 * @param options
 * @param settings
 */
async function createPrompt(options, settings) {
    // override cancel callback
    let cancelCallback;
    /* istanbul ignore if */
    if (settings === null || settings === void 0 ? void 0 : settings.cancelCallback) {
        cancelCallback = settings.cancelCallback;
    } /* istanbul ignore next */
    else {
        cancelCallback = defaultCancelCallback;
    }
    // assign default if there is single prompt
    if (!Array.isArray(options)) {
        options = [{ ...options, name: 'default' }];
    } /* istanbul ignore next */
    else if (options.length === 1) {
        options = options.reduce((o, option) => {
            return [...o, Object.assign(option, { name: 'default' })];
        }, []);
    }
    // assign default enquirer options
    options = options.reduce((o, option) => {
        var _a;
        return [
            ...o,
            Object.assign(option, {
                // this is for outside calls, if it is not called from taskwrapper with bind
                stdout: this instanceof task_wrapper_1.TaskWrapper ? (_a = settings === null || settings === void 0 ? void 0 : settings.stdout) !== null && _a !== void 0 ? _a : this.stdout() : process.stdout,
                onCancel: cancelCallback.bind(this, settings)
            })
        ];
    }, []);
    let enquirer;
    if (settings === null || settings === void 0 ? void 0 : settings.enquirer) {
        // injected enquirer
        enquirer = settings.enquirer;
    }
    else {
        try {
            enquirer = new (await Promise.resolve().then(() => require('enquirer')))();
        } /* istanbul ignore next */
        catch (e) {
            this.task.prompt = new listr_error_interface_1.PromptError('Enquirer is a peer dependency that must be installed separately.');
            throw new Error(e);
        }
    }
    // i use this externally as well, this is a bandaid
    if (this instanceof task_wrapper_1.TaskWrapper) {
        // Capture the prompt instance so we can use it later
        enquirer.on('prompt', (prompt) => this.task.prompt = prompt);
        // Clear the prompt instance once it's submitted
        // Can't use on cancel, since that might hold a PromptError object
        enquirer.on('submit', () => this.task.prompt = undefined);
        this.task.subscribe((event) => {
            if (event.type === event_constants_1.ListrEventType.STATE && event.data === state_constants_1.ListrTaskState.SKIPPED) {
                if (this.task.prompt && !(this.task.prompt instanceof listr_error_interface_1.PromptError)) {
                    this.task.prompt.submit();
                }
            }
        });
    }
    const response = (await enquirer.prompt(options));
    // return default name if it is single prompt
    if (options.length === 1) {
        return response.default;
    }
    else {
        return response;
    }
}
exports.createPrompt = createPrompt;
function destroyPrompt(throwError = false) {
    if (!this.task.prompt || this.task.prompt instanceof listr_error_interface_1.PromptError) {
        // If there's no prompt, can't cancel
        return;
    }
    if (throwError) {
        this.task.prompt.cancel();
    }
    else {
        this.task.prompt.submit();
    }
}
exports.destroyPrompt = destroyPrompt;
function defaultCancelCallback(settings) {
    const errorMsg = 'Cancelled prompt.';
    if (this instanceof task_wrapper_1.TaskWrapper) {
        this.task.prompt = new listr_error_interface_1.PromptError(errorMsg);
    } /* istanbul ignore next */
    else if ((settings === null || settings === void 0 ? void 0 : settings.error) !== false) {
        throw new Error(errorMsg);
    } /* istanbul ignore next */
    else {
        return errorMsg;
    }
}
