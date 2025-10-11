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

// src/queriesObserver.ts
var queriesObserver_exports = {};
__export(queriesObserver_exports, {
  QueriesObserver: () => QueriesObserver
});
module.exports = __toCommonJS(queriesObserver_exports);
var import_notifyManager = require("./notifyManager.cjs");
var import_queryObserver = require("./queryObserver.cjs");
var import_subscribable = require("./subscribable.cjs");
var import_utils = require("./utils.cjs");
function difference(array1, array2) {
  const excludeSet = new Set(array2);
  return array1.filter((x) => !excludeSet.has(x));
}
function replaceAt(array, index, value) {
  const copy = array.slice(0);
  copy[index] = value;
  return copy;
}
var QueriesObserver = class extends import_subscribable.Subscribable {
  #client;
  #result;
  #queries;
  #options;
  #observers;
  #combinedResult;
  #lastCombine;
  #lastResult;
  #observerMatches = [];
  constructor(client, queries, options) {
    super();
    this.#client = client;
    this.#options = options;
    this.#queries = [];
    this.#observers = [];
    this.#result = [];
    this.setQueries(queries);
  }
  onSubscribe() {
    if (this.listeners.size === 1) {
      this.#observers.forEach((observer) => {
        observer.subscribe((result) => {
          this.#onUpdate(observer, result);
        });
      });
    }
  }
  onUnsubscribe() {
    if (!this.listeners.size) {
      this.destroy();
    }
  }
  destroy() {
    this.listeners = /* @__PURE__ */ new Set();
    this.#observers.forEach((observer) => {
      observer.destroy();
    });
  }
  setQueries(queries, options) {
    this.#queries = queries;
    this.#options = options;
    if (process.env.NODE_ENV !== "production") {
      const queryHashes = queries.map(
        (query) => this.#client.defaultQueryOptions(query).queryHash
      );
      if (new Set(queryHashes).size !== queryHashes.length) {
        console.warn(
          "[QueriesObserver]: Duplicate Queries found. This might result in unexpected behavior."
        );
      }
    }
    import_notifyManager.notifyManager.batch(() => {
      const prevObservers = this.#observers;
      const newObserverMatches = this.#findMatchingObservers(this.#queries);
      this.#observerMatches = newObserverMatches;
      newObserverMatches.forEach(
        (match) => match.observer.setOptions(match.defaultedQueryOptions)
      );
      const newObservers = newObserverMatches.map((match) => match.observer);
      const newResult = newObservers.map(
        (observer) => observer.getCurrentResult()
      );
      const hasLengthChange = prevObservers.length !== newObservers.length;
      const hasIndexChange = newObservers.some(
        (observer, index) => observer !== prevObservers[index]
      );
      const hasStructuralChange = hasLengthChange || hasIndexChange;
      const hasResultChange = hasStructuralChange ? true : newResult.some((result, index) => {
        const prev = this.#result[index];
        return !prev || !(0, import_utils.shallowEqualObjects)(result, prev);
      });
      if (!hasStructuralChange && !hasResultChange) return;
      if (hasStructuralChange) {
        this.#observers = newObservers;
      }
      this.#result = newResult;
      if (!this.hasListeners()) return;
      if (hasStructuralChange) {
        difference(prevObservers, newObservers).forEach((observer) => {
          observer.destroy();
        });
        difference(newObservers, prevObservers).forEach((observer) => {
          observer.subscribe((result) => {
            this.#onUpdate(observer, result);
          });
        });
      }
      this.#notify();
    });
  }
  getCurrentResult() {
    return this.#result;
  }
  getQueries() {
    return this.#observers.map((observer) => observer.getCurrentQuery());
  }
  getObservers() {
    return this.#observers;
  }
  getOptimisticResult(queries, combine) {
    const matches = this.#findMatchingObservers(queries);
    const result = matches.map(
      (match) => match.observer.getOptimisticResult(match.defaultedQueryOptions)
    );
    return [
      result,
      (r) => {
        return this.#combineResult(r ?? result, combine);
      },
      () => {
        return this.#trackResult(result, matches);
      }
    ];
  }
  #trackResult(result, matches) {
    return matches.map((match, index) => {
      const observerResult = result[index];
      return !match.defaultedQueryOptions.notifyOnChangeProps ? match.observer.trackResult(observerResult, (accessedProp) => {
        matches.forEach((m) => {
          m.observer.trackProp(accessedProp);
        });
      }) : observerResult;
    });
  }
  #combineResult(input, combine) {
    if (combine) {
      if (!this.#combinedResult || this.#result !== this.#lastResult || combine !== this.#lastCombine) {
        this.#lastCombine = combine;
        this.#lastResult = this.#result;
        this.#combinedResult = (0, import_utils.replaceEqualDeep)(
          this.#combinedResult,
          combine(input)
        );
      }
      return this.#combinedResult;
    }
    return input;
  }
  #findMatchingObservers(queries) {
    const prevObserversMap = new Map(
      this.#observers.map((observer) => [observer.options.queryHash, observer])
    );
    const observers = [];
    queries.forEach((options) => {
      const defaultedOptions = this.#client.defaultQueryOptions(options);
      const match = prevObserversMap.get(defaultedOptions.queryHash);
      if (match) {
        observers.push({
          defaultedQueryOptions: defaultedOptions,
          observer: match
        });
      } else {
        observers.push({
          defaultedQueryOptions: defaultedOptions,
          observer: new import_queryObserver.QueryObserver(this.#client, defaultedOptions)
        });
      }
    });
    return observers;
  }
  #onUpdate(observer, result) {
    const index = this.#observers.indexOf(observer);
    if (index !== -1) {
      this.#result = replaceAt(this.#result, index, result);
      this.#notify();
    }
  }
  #notify() {
    if (this.hasListeners()) {
      const previousResult = this.#combinedResult;
      const newTracked = this.#trackResult(this.#result, this.#observerMatches);
      const newResult = this.#combineResult(newTracked, this.#options?.combine);
      if (previousResult !== newResult) {
        import_notifyManager.notifyManager.batch(() => {
          this.listeners.forEach((listener) => {
            listener(this.#result);
          });
        });
      }
    }
  }
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  QueriesObserver
});
//# sourceMappingURL=queriesObserver.cjs.map