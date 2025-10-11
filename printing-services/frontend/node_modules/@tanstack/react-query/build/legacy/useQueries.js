"use client";

// src/useQueries.ts
import * as React from "react";
import {
  QueriesObserver,
  QueryObserver,
  noop,
  notifyManager
} from "@tanstack/query-core";
import { useQueryClient } from "./QueryClientProvider.js";
import { useIsRestoring } from "./IsRestoringProvider.js";
import { useQueryErrorResetBoundary } from "./QueryErrorResetBoundary.js";
import {
  ensurePreventErrorBoundaryRetry,
  getHasError,
  useClearResetErrorBoundary
} from "./errorBoundaryUtils.js";
import {
  ensureSuspenseTimers,
  fetchOptimistic,
  shouldSuspend,
  willFetch
} from "./suspense.js";
function useQueries({
  queries,
  ...options
}, queryClient) {
  const client = useQueryClient(queryClient);
  const isRestoring = useIsRestoring();
  const errorResetBoundary = useQueryErrorResetBoundary();
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
    ensureSuspenseTimers(query);
    ensurePreventErrorBoundaryRetry(query, errorResetBoundary);
  });
  useClearResetErrorBoundary(errorResetBoundary);
  const [observer] = React.useState(
    () => new QueriesObserver(
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
      (onStoreChange) => shouldSubscribe ? observer.subscribe(notifyManager.batchCalls(onStoreChange)) : noop,
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
    (result, index) => shouldSuspend(defaultedQueries[index], result)
  );
  const suspensePromises = shouldAtLeastOneSuspend ? optimisticResult.flatMap((result, index) => {
    const opts = defaultedQueries[index];
    if (opts) {
      const queryObserver = new QueryObserver(client, opts);
      if (shouldSuspend(opts, result)) {
        return fetchOptimistic(opts, queryObserver, errorResetBoundary);
      } else if (willFetch(result, isRestoring)) {
        void fetchOptimistic(opts, queryObserver, errorResetBoundary);
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
      return query && getHasError({
        result,
        errorResetBoundary,
        throwOnError: query.throwOnError,
        query: client.getQueryCache().get(query.queryHash),
        suspense: query.suspense
      });
    }
  );
  if (firstSingleResultWhichShouldThrow == null ? void 0 : firstSingleResultWhichShouldThrow.error) {
    throw firstSingleResultWhichShouldThrow.error;
  }
  return getCombinedResult(trackResult());
}
export {
  useQueries
};
//# sourceMappingURL=useQueries.js.map