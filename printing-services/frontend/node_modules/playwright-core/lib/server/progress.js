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
var progress_exports = {};
__export(progress_exports, {
  ProgressController: () => ProgressController,
  isAbortError: () => isAbortError,
  raceUncancellableOperationWithCleanup: () => raceUncancellableOperationWithCleanup
});
module.exports = __toCommonJS(progress_exports);
var import_errors = require("./errors");
var import_utils = require("../utils");
var import_manualPromise = require("../utils/isomorphic/manualPromise");
class ProgressController {
  constructor(metadata, onCallLog) {
    this._forceAbortPromise = new import_manualPromise.ManualPromise();
    this._donePromise = new import_manualPromise.ManualPromise();
    this._state = "before";
    this.metadata = metadata || { id: "", startTime: 0, endTime: 0, type: "Internal", method: "", params: {}, log: [], internal: true };
    this._onCallLog = onCallLog;
    this._forceAbortPromise.catch((e) => null);
  }
  async abort(error) {
    if (this._state === "running") {
      error[kAbortErrorSymbol] = true;
      this._state = { error };
      this._forceAbortPromise.reject(error);
    }
    await this._donePromise;
  }
  async run(task, timeout) {
    (0, import_utils.assert)(this._state === "before");
    this._state = "running";
    const progress = {
      log: (message) => {
        if (this._state === "running")
          this.metadata.log.push(message);
        this._onCallLog?.(message);
      },
      metadata: this.metadata,
      race: (promise) => {
        const promises = Array.isArray(promise) ? promise : [promise];
        return Promise.race([...promises, this._forceAbortPromise]);
      },
      wait: async (timeout2) => {
        let timer2;
        const promise = new Promise((f) => timer2 = setTimeout(f, timeout2));
        return progress.race(promise).finally(() => clearTimeout(timer2));
      }
    };
    let timer;
    if (timeout) {
      const timeoutError = new import_errors.TimeoutError(`Timeout ${timeout}ms exceeded.`);
      timer = setTimeout(() => {
        if (this._state === "running") {
          timeoutError[kAbortErrorSymbol] = true;
          this._state = { error: timeoutError };
          this._forceAbortPromise.reject(timeoutError);
        }
      }, timeout);
    }
    try {
      const result = await task(progress);
      this._state = "finished";
      return result;
    } catch (error) {
      this._state = { error };
      throw error;
    } finally {
      clearTimeout(timer);
      this._donePromise.resolve();
    }
  }
}
const kAbortErrorSymbol = Symbol("kAbortError");
function isAbortError(error) {
  return !!error[kAbortErrorSymbol];
}
async function raceUncancellableOperationWithCleanup(progress, run, cleanup) {
  let aborted = false;
  try {
    return await progress.race(run().then(async (t) => {
      if (aborted)
        await cleanup(t);
      return t;
    }));
  } catch (error) {
    aborted = true;
    throw error;
  }
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ProgressController,
  isAbortError,
  raceUncancellableOperationWithCleanup
});
