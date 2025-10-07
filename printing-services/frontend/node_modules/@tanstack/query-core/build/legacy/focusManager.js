import {
  __privateAdd,
  __privateGet,
  __privateSet
} from "./chunk-PXG64RU4.js";

// src/focusManager.ts
import { Subscribable } from "./subscribable.js";
import { isServer } from "./utils.js";
var _focused, _cleanup, _setup;
var FocusManager = class extends Subscribable {
  constructor() {
    super();
    __privateAdd(this, _focused);
    __privateAdd(this, _cleanup);
    __privateAdd(this, _setup);
    __privateSet(this, _setup, (onFocus) => {
      if (!isServer && window.addEventListener) {
        const listener = () => onFocus();
        window.addEventListener("visibilitychange", listener, false);
        return () => {
          window.removeEventListener("visibilitychange", listener);
        };
      }
      return;
    });
  }
  onSubscribe() {
    if (!__privateGet(this, _cleanup)) {
      this.setEventListener(__privateGet(this, _setup));
    }
  }
  onUnsubscribe() {
    var _a;
    if (!this.hasListeners()) {
      (_a = __privateGet(this, _cleanup)) == null ? void 0 : _a.call(this);
      __privateSet(this, _cleanup, void 0);
    }
  }
  setEventListener(setup) {
    var _a;
    __privateSet(this, _setup, setup);
    (_a = __privateGet(this, _cleanup)) == null ? void 0 : _a.call(this);
    __privateSet(this, _cleanup, setup((focused) => {
      if (typeof focused === "boolean") {
        this.setFocused(focused);
      } else {
        this.onFocus();
      }
    }));
  }
  setFocused(focused) {
    const changed = __privateGet(this, _focused) !== focused;
    if (changed) {
      __privateSet(this, _focused, focused);
      this.onFocus();
    }
  }
  onFocus() {
    const isFocused = this.isFocused();
    this.listeners.forEach((listener) => {
      listener(isFocused);
    });
  }
  isFocused() {
    var _a;
    if (typeof __privateGet(this, _focused) === "boolean") {
      return __privateGet(this, _focused);
    }
    return ((_a = globalThis.document) == null ? void 0 : _a.visibilityState) !== "hidden";
  }
};
_focused = new WeakMap();
_cleanup = new WeakMap();
_setup = new WeakMap();
var focusManager = new FocusManager();
export {
  FocusManager,
  focusManager
};
//# sourceMappingURL=focusManager.js.map