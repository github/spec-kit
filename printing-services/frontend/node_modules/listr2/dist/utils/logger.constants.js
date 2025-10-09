"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LogLevels = void 0;
/** Default loglevels for the logger */
var LogLevels;
(function (LogLevels) {
    LogLevels["SILENT"] = "SILENT";
    LogLevels["FAILED"] = "FAILED";
    LogLevels["SKIPPED"] = "SKIPPED";
    LogLevels["SUCCESS"] = "SUCCESS";
    LogLevels["DATA"] = "DATA";
    LogLevels["STARTED"] = "STARTED";
    LogLevels["TITLE"] = "TITLE";
    LogLevels["RETRY"] = "RETRY";
    LogLevels["ROLLBACK"] = "ROLLBACK";
})(LogLevels = exports.LogLevels || (exports.LogLevels = {}));
