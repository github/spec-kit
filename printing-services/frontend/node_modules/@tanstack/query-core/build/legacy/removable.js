import {
  __privateAdd,
  __privateGet,
  __privateSet
} from "./chunk-PXG64RU4.js";

// src/removable.ts
import { timeoutManager } from "./timeoutManager.js";
import { isServer, isValidTimeout } from "./utils.js";
var _gcTimeout;
var Removable = class {
  constructor() {
    __privateAdd(this, _gcTimeout);
  }
  destroy() {
    this.clearGcTimeout();
  }
  scheduleGc() {
    this.clearGcTimeout();
    if (isValidTimeout(this.gcTime)) {
      __privateSet(this, _gcTimeout, timeoutManager.setTimeout(() => {
        this.optionalRemove();
      }, this.gcTime));
    }
  }
  updateGcTime(newGcTime) {
    this.gcTime = Math.max(
      this.gcTime || 0,
      newGcTime ?? (isServer ? Infinity : 5 * 60 * 1e3)
    );
  }
  clearGcTimeout() {
    if (__privateGet(this, _gcTimeout)) {
      timeoutManager.clearTimeout(__privateGet(this, _gcTimeout));
      __privateSet(this, _gcTimeout, void 0);
    }
  }
};
_gcTimeout = new WeakMap();
export {
  Removable
};
//# sourceMappingURL=removable.js.map