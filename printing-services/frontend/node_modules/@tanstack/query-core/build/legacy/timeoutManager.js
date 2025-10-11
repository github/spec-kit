import {
  __privateAdd,
  __privateGet,
  __privateSet
} from "./chunk-PXG64RU4.js";

// src/timeoutManager.ts
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
export {
  TimeoutManager,
  defaultTimeoutProvider,
  systemSetTimeoutZero,
  timeoutManager
};
//# sourceMappingURL=timeoutManager.js.map