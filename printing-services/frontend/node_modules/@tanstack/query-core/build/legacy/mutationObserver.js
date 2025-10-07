import {
  __privateAdd,
  __privateGet,
  __privateMethod,
  __privateSet
} from "./chunk-PXG64RU4.js";

// src/mutationObserver.ts
import { getDefaultState } from "./mutation.js";
import { notifyManager } from "./notifyManager.js";
import { Subscribable } from "./subscribable.js";
import { hashKey, shallowEqualObjects } from "./utils.js";
var _client, _currentResult, _currentMutation, _mutateOptions, _MutationObserver_instances, updateResult_fn, notify_fn;
var MutationObserver = class extends Subscribable {
  constructor(client, options) {
    super();
    __privateAdd(this, _MutationObserver_instances);
    __privateAdd(this, _client);
    __privateAdd(this, _currentResult);
    __privateAdd(this, _currentMutation);
    __privateAdd(this, _mutateOptions);
    __privateSet(this, _client, client);
    this.setOptions(options);
    this.bindMethods();
    __privateMethod(this, _MutationObserver_instances, updateResult_fn).call(this);
  }
  bindMethods() {
    this.mutate = this.mutate.bind(this);
    this.reset = this.reset.bind(this);
  }
  setOptions(options) {
    var _a;
    const prevOptions = this.options;
    this.options = __privateGet(this, _client).defaultMutationOptions(options);
    if (!shallowEqualObjects(this.options, prevOptions)) {
      __privateGet(this, _client).getMutationCache().notify({
        type: "observerOptionsUpdated",
        mutation: __privateGet(this, _currentMutation),
        observer: this
      });
    }
    if ((prevOptions == null ? void 0 : prevOptions.mutationKey) && this.options.mutationKey && hashKey(prevOptions.mutationKey) !== hashKey(this.options.mutationKey)) {
      this.reset();
    } else if (((_a = __privateGet(this, _currentMutation)) == null ? void 0 : _a.state.status) === "pending") {
      __privateGet(this, _currentMutation).setOptions(this.options);
    }
  }
  onUnsubscribe() {
    var _a;
    if (!this.hasListeners()) {
      (_a = __privateGet(this, _currentMutation)) == null ? void 0 : _a.removeObserver(this);
    }
  }
  onMutationUpdate(action) {
    __privateMethod(this, _MutationObserver_instances, updateResult_fn).call(this);
    __privateMethod(this, _MutationObserver_instances, notify_fn).call(this, action);
  }
  getCurrentResult() {
    return __privateGet(this, _currentResult);
  }
  reset() {
    var _a;
    (_a = __privateGet(this, _currentMutation)) == null ? void 0 : _a.removeObserver(this);
    __privateSet(this, _currentMutation, void 0);
    __privateMethod(this, _MutationObserver_instances, updateResult_fn).call(this);
    __privateMethod(this, _MutationObserver_instances, notify_fn).call(this);
  }
  mutate(variables, options) {
    var _a;
    __privateSet(this, _mutateOptions, options);
    (_a = __privateGet(this, _currentMutation)) == null ? void 0 : _a.removeObserver(this);
    __privateSet(this, _currentMutation, __privateGet(this, _client).getMutationCache().build(__privateGet(this, _client), this.options));
    __privateGet(this, _currentMutation).addObserver(this);
    return __privateGet(this, _currentMutation).execute(variables);
  }
};
_client = new WeakMap();
_currentResult = new WeakMap();
_currentMutation = new WeakMap();
_mutateOptions = new WeakMap();
_MutationObserver_instances = new WeakSet();
updateResult_fn = function() {
  var _a;
  const state = ((_a = __privateGet(this, _currentMutation)) == null ? void 0 : _a.state) ?? getDefaultState();
  __privateSet(this, _currentResult, {
    ...state,
    isPending: state.status === "pending",
    isSuccess: state.status === "success",
    isError: state.status === "error",
    isIdle: state.status === "idle",
    mutate: this.mutate,
    reset: this.reset
  });
};
notify_fn = function(action) {
  notifyManager.batch(() => {
    var _a, _b, _c, _d, _e, _f, _g, _h;
    if (__privateGet(this, _mutateOptions) && this.hasListeners()) {
      const variables = __privateGet(this, _currentResult).variables;
      const onMutateResult = __privateGet(this, _currentResult).context;
      const context = {
        client: __privateGet(this, _client),
        meta: this.options.meta,
        mutationKey: this.options.mutationKey
      };
      if ((action == null ? void 0 : action.type) === "success") {
        (_b = (_a = __privateGet(this, _mutateOptions)).onSuccess) == null ? void 0 : _b.call(
          _a,
          action.data,
          variables,
          onMutateResult,
          context
        );
        (_d = (_c = __privateGet(this, _mutateOptions)).onSettled) == null ? void 0 : _d.call(
          _c,
          action.data,
          null,
          variables,
          onMutateResult,
          context
        );
      } else if ((action == null ? void 0 : action.type) === "error") {
        (_f = (_e = __privateGet(this, _mutateOptions)).onError) == null ? void 0 : _f.call(
          _e,
          action.error,
          variables,
          onMutateResult,
          context
        );
        (_h = (_g = __privateGet(this, _mutateOptions)).onSettled) == null ? void 0 : _h.call(
          _g,
          void 0,
          action.error,
          variables,
          onMutateResult,
          context
        );
      }
    }
    this.listeners.forEach((listener) => {
      listener(__privateGet(this, _currentResult));
    });
  });
};
export {
  MutationObserver
};
//# sourceMappingURL=mutationObserver.js.map