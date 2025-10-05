"use strict";
"use client";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
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
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/useQueries.ts
var useQueries_exports = {};
__export(useQueries_exports, {
  useQueries: () => useQueries
});
module.exports = __toCommonJS(useQueries_exports);
var React = __toESM(require("react"), 1);
var import_query_core = require("@tanstack/query-core");
var import_QueryClientProvider = require("./QueryClientProvider.cjs");
var import_IsRestoringProvider = require("./IsRestoringProvider.cjs");
var import_QueryErrorResetBoundary = require("./QueryErrorResetBoundary.cjs");
var import_errorBoundaryUtils = require("./errorBoundaryUtils.cjs");
var import_suspense = require("./suspense.cjs");
function useQueries({
  queries,
  ...options
}, queryClient) {
  const client = (0, import_QueryClientProvider.useQueryClient)(queryClient);
  const isRestoring = (0, import_IsRestoringProvider.useIsRestoring)();
  const errorResetBoundary = (0, import_QueryErrorResetBoundary.useQueryErrorResetBoundary)();
  const defaultedQueries = React.useMemo(
    () => queries.map((opts) => {
      const defaultedOptions = client.defaultQueryOptions(
        opts
      );
      defaultedOptions._optimisticResults = isRestoring ? "isRestoring" : "optimistic";
      return defaultedOptions;
    }),
    [queries, client, isRestoring]
  );
  defaultedQueries.forEach((query) => {
    (0, import_suspense.ensureSuspenseTimers)(query);
    (0, import_errorBoundaryUtils.ensurePreventErrorBoundaryRetry)(query, errorResetBoundary);
  });
  (0, import_errorBoundaryUtils.useClearResetErrorBoundary)(errorResetBoundary);
  const [observer] = React.useState(
    () => new import_query_core.QueriesObserver(
      client,
      defaultedQueries,
      options
    )
  );
  const [optimisticResult, getCombinedResult, trackResult] = observer.getOptimisticResult(
    defaultedQueries,
    options.combine
  );
  const shouldSubscribe = !isRestoring && options.subscribed !== false;
  React.useSyncExternalStore(
    React.useCallback(
      (onStoreChange) => shouldSubscribe ? observer.subscribe(import_query_core.notifyManager.batchCalls(onStoreChange)) : import_query_core.noop,
      [observer, shouldSubscribe]
    ),
    () => observer.getCurrentResult(),
    () => observer.getCurrentResult()
  );
  React.useEffect(() => {
    observer.setQueries(
      defaultedQueries,
      options
    );
  }, [defaultedQueries, options, observer]);
  const shouldAtLeastOneSuspend = optimisticResult.some(
    (result, index) => (0, import_suspense.shouldSuspend)(defaultedQueries[index], result)
  );
  const suspensePromises = shouldAtLeastOneSuspend ? optimisticResult.flatMap((result, index) => {
    const opts = defaultedQueries[index];
    if (opts) {
      const queryObserver = new import_query_core.QueryObserver(client, opts);
      if ((0, import_suspense.shouldSuspend)(opts, result)) {
        return (0, import_suspense.fetchOptimistic)(opts, queryObserver, errorResetBoundary);
      } else if ((0, import_suspense.willFetch)(result, isRestoring)) {
        void (0, import_suspense.fetchOptimistic)(opts, queryObserver, errorResetBoundary);
      }
    }
    return [];
  }) : [];
  if (suspensePromises.length > 0) {
    throw Promise.all(suspensePromises);
  }
  const firstSingleResultWhichShouldThrow = optimisticResult.find(
    (result, index) => {
      const query = defaultedQueries[index];
      return query && (0, import_errorBoundaryUtils.getHasError)({
        result,
        errorResetBoundary,
        throwOnError: query.throwOnError,
        query: client.getQueryCache().get(query.queryHash),
        suspense: query.suspense
      });
    }
  );
  if (firstSingleResultWhichShouldThrow?.error) {
    throw firstSingleResultWhichShouldThrow.error;
  }
  return getCombinedResult(trackResult());
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  useQueries
});
//# sourceMappingURL=useQueries.cjs.map