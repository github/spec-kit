"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ListrTaskState = void 0;
/** Available task states. */
var ListrTaskState;
(function (ListrTaskState) {
    ListrTaskState["PENDING"] = "PENDING";
    ListrTaskState["COMPLETED"] = "COMPLETED";
    ListrTaskState["FAILED"] = "FAILED";
    ListrTaskState["SKIPPED"] = "SKIPPED";
    ListrTaskState["ROLLING_BACK"] = "ROLLING_BACK";
    ListrTaskState["ROLLED_BACK"] = "ROLLED_BACK";
    ListrTaskState["RETRY"] = "RETRY";
})(ListrTaskState = exports.ListrTaskState || (exports.ListrTaskState = {}));
