"use strict";
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __typeError = (msg) => {
  throw TypeError(msg);
};
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
var __accessCheck = (obj, member, msg) => member.has(obj) || __typeError("Cannot " + msg);
var __privateGet = (obj, member, getter) => (__accessCheck(obj, member, "read from private field"), getter ? getter.call(obj) : member.get(obj));
var __privateAdd = (obj, member, value) => member.has(obj) ? __typeError("Cannot add the same private member more than once") : member instanceof WeakSet ? member.add(obj) : member.set(obj, value);
var __privateSet = (obj, member, value, setter) => (__accessCheck(obj, member, "write to private field"), setter ? setter.call(obj, value) : member.set(obj, value), value);

// src/timeoutManager.ts
var timeoutManager_exports = {};
__export(timeoutManager_exports, {
  TimeoutManager: () => TimeoutManager,
  defaultTimeoutProvider: () => defaultTimeoutProvider,
  systemSetTimeoutZero: () => systemSetTimeoutZero,
  timeoutManager: () => timeoutManager
});
module.exports = __toCommonJS(timeoutManager_exports);
var defaultTimeoutProvider = {
  // We need the wrapper function syntax below instead of direct references to
  // global setTimeout etc.
  //
  // BAD: `setTimeout: setTimeout`
  // GOOD: `setTimeout: (cb, delay) => setTimeout(cb, delay)`
  //
  // If we use direct references here, then anything that wants to spy on or
  // replace the global setTimeout (like tests) won't work since we'll already
  // have a hard reference to the original implementation at the time when this
  // file was imported.
  setTimeout: (callback, delay) => setTimeout(callback, delay),
  clearTimeout: (timeoutId) => clearTimeout(timeoutId),
  setInterval: (callback, delay) => setInterval(callback, delay),
  clearInterval: (intervalId) => clearInterval(intervalId)
};
var _provider, _providerCalled;
var TimeoutManager = class {
  constructor() {
    // We cannot have TimeoutManager<T> as we must instantiate it with a concrete
    // type at app boot; and if we leave that type, then any new timer provider
    // would need to support ReturnType<typeof setTimeout>, which is infeasible.
    //
    // We settle for type safety for the TimeoutProvider type, and accept that
    // this class is unsafe internally to allow for extension.
    __privateAdd(this, _provider, defaultTimeoutProvider);
    __privateAdd(this, _providerCalled, false);
  }
  setTimeoutProvider(provider) {
    if (process.env.NODE_ENV !== "production") {
      if (__privateGet(this, _providerCalled) && provider !== __privateGet(this, _provider)) {
        console.error(
          `[timeoutManager]: Switching provider after calls to previous provider might result in unexpected behavior.`,
          { previous: __privateGet(this, _provider), provider }
        );
      }
    }
    __privateSet(this, _provider, provider);
    if (process.env.NODE_ENV !== "production") {
      __privateSet(this, _providerCalled, false);
    }
  }
  setTimeout(callback, delay) {
    if (process.env.NODE_ENV !== "production") {
      __privateSet(this, _providerCalled, true);
    }
    return __privateGet(this, _provider).setTimeout(callback, delay);
  }
  clearTimeout(timeoutId) {
    __privateGet(this, _provider).clearTimeout(timeoutId);
  }
  setInterval(callback, delay) {
    if (process.env.NODE_ENV !== "production") {
      __privateSet(this, _providerCalled, true);
    }
    return __privateGet(this, _provider).setInterval(callback, delay);
  }
  clearInterval(intervalId) {
    __privateGet(this, _provider).clearInterval(intervalId);
  }
};
_provider = new WeakMap();
_providerCalled = new WeakMap();
var timeoutManager = new TimeoutManager();
function systemSetTimeoutZero(callback) {
  setTimeout(callback, 0);
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  TimeoutManager,
  defaultTimeoutProvider,
  systemSetTimeoutZero,
  timeoutManager
});
//# sourceMappingURL=timeoutManager.cjs.map