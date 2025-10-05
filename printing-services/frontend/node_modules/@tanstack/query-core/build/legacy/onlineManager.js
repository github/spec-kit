import {
  __privateAdd,
  __privateGet,
  __privateSet
} from "./chunk-PXG64RU4.js";

// src/onlineManager.ts
import { Subscribable } from "./subscribable.js";
import { isServer } from "./utils.js";
var _online, _cleanup, _setup;
var OnlineManager = class extends Subscribable {
  constructor() {
    super();
    __privateAdd(this, _online, true);
    __privateAdd(this, _cleanup);
    __privateAdd(this, _setup);
    __privateSet(this, _setup, (onOnline) => {
      if (!isServer && window.addEventListener) {
        const onlineListener = () => onOnline(true);
        const offlineListener = () => onOnline(false);
        window.addEventListener("online", onlineListener, false);
        window.addEventListener("offline", offlineListener, false);
        return () => {
          window.removeEventListener("online", onlineListener);
          window.removeEventListener("offline", offlineListener);
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
    __privateSet(this, _cleanup, setup(this.setOnline.bind(this)));
  }
  setOnline(online) {
    const changed = __privateGet(this, _online) !== online;
    if (changed) {
      __privateSet(this, _online, online);
      this.listeners.forEach((listener) => {
        listener(online);
      });
    }
  }
  isOnline() {
    return __privateGet(this, _online);
  }
};
_online = new WeakMap();
_cleanup = new WeakMap();
_setup = new WeakMap();
var onlineManager = new OnlineManager();
export {
  OnlineManager,
  onlineManager
};
//# sourceMappingURL=onlineManager.js.map