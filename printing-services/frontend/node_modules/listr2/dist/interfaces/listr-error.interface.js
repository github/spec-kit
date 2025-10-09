"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PromptError = exports.ListrErrorTypes = exports.ListrError = void 0;
/** The internal error handling mechanism.. */
class ListrError extends Error {
    constructor(error, type, ctx, task) {
        super(error.message);
        this.error = error;
        this.type = type;
        this.ctx = ctx;
        this.task = task;
        this.stack = error === null || error === void 0 ? void 0 : error.stack;
        this.name = 'ListrError';
    }
}
exports.ListrError = ListrError;
/**
 * The actual error type that is collected and to help identify where the error is triggered from.
 */
var ListrErrorTypes;
(function (ListrErrorTypes) {
    /** Task has failed and will try to retry. */
    ListrErrorTypes["WILL_RETRY"] = "WILL_RETRY";
    /** Task has failed and will try to rollback. */
    ListrErrorTypes["WILL_ROLLBACK"] = "WILL_ROLLBACK";
    /** Task has failed, ran the rollback action but the rollback action itself has failed. */
    ListrErrorTypes["HAS_FAILED_TO_ROLLBACK"] = "HAS_FAILED_TO_ROLLBACK";
    /** Task has failed. */
    ListrErrorTypes["HAS_FAILED"] = "HAS_FAILED";
    /** Task has failed, but exitOnError is set to false, so will ignore this error. */
    ListrErrorTypes["HAS_FAILED_WITHOUT_ERROR"] = "HAS_FAILED_WITHOUT_ERROR";
})(ListrErrorTypes = exports.ListrErrorTypes || (exports.ListrErrorTypes = {}));
/** The internal error handling mechanism for prompts only. */
class PromptError extends Error {
    constructor(message) {
        super(message);
        this.name = 'PromptError';
    }
}
exports.PromptError = PromptError;
