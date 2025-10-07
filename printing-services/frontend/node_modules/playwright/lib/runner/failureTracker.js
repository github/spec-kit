"use strict";
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);
var failureTracker_exports = {};
__export(failureTracker_exports, {
  FailureTracker: () => FailureTracker
});
module.exports = __toCommonJS(failureTracker_exports);
class FailureTracker {
  constructor(_config) {
    this._config = _config;
    this._failureCount = 0;
    this._hasWorkerErrors = false;
  }
  canRecoverFromStepError() {
    return !!this._recoverFromStepErrorHandler;
  }
  setRecoverFromStepErrorHandler(recoverFromStepErrorHandler) {
    this._recoverFromStepErrorHandler = recoverFromStepErrorHandler;
  }
  onRootSuite(rootSuite) {
    this._rootSuite = rootSuite;
  }
  onTestEnd(test, result) {
    if (test.outcome() === "unexpected" && test.results.length > test.retries)
      ++this._failureCount;
  }
  recoverFromStepError(stepId, error, resumeAfterStepError) {
    if (!this._recoverFromStepErrorHandler) {
      resumeAfterStepError({ stepId, status: "failed" });
      return;
    }
    void this._recoverFromStepErrorHandler(stepId, error).then(resumeAfterStepError).catch(() => {
    });
  }
  onWorkerError() {
    this._hasWorkerErrors = true;
  }
  hasReachedMaxFailures() {
    return this.maxFailures() > 0 && this._failureCount >= this.maxFailures();
  }
  hasWorkerErrors() {
    return this._hasWorkerErrors;
  }
  result() {
    return this._hasWorkerErrors || this.hasReachedMaxFailures() || this.hasFailedTests() || this._config.failOnFlakyTests && this.hasFlakyTests() ? "failed" : "passed";
  }
  hasFailedTests() {
    return this._rootSuite?.allTests().some((test) => !test.ok());
  }
  hasFlakyTests() {
    return this._rootSuite?.allTests().some((test) => test.outcome() === "flaky");
  }
  maxFailures() {
    return this._config.config.maxFailures;
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  FailureTracker
});
