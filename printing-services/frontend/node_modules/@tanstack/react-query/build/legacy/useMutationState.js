"use client";

// src/useMutationState.ts
import * as React from "react";
import { notifyManager, replaceEqualDeep } from "@tanstack/query-core";
import { useQueryClient } from "./QueryClientProvider.js";
function useIsMutating(filters, queryClient) {
  const client = useQueryClient(queryClient);
  return useMutationState(
    { filters: { ...filters, status: "pending" } },
    client
  ).length;
}
function getResult(mutationCache, options) {
  return mutationCache.findAll(options.filters).map(
    (mutation) => options.select ? options.select(mutation) : mutation.state
  );
}
function useMutationState(options = {}, queryClient) {
  const mutationCache = useQueryClient(queryClient).getMutationCache();
  const optionsRef = React.useRef(options);
  const result = React.useRef(null);
  if (!result.current) {
    result.current = getResult(mutationCache, options);
  }
  React.useEffect(() => {
    optionsRef.current = options;
  });
  return React.useSyncExternalStore(
    React.useCallback(
      (onStoreChange) => mutationCache.subscribe(() => {
        const nextResult = replaceEqualDeep(
          result.current,
          getResult(mutationCache, optionsRef.current)
        );
        if (result.current !== nextResult) {
          result.current = nextResult;
          notifyManager.schedule(onStoreChange);
        }
      }),
      [mutationCache]
    ),
    () => result.current,
    () => result.current
  );
}
export {
  useIsMutating,
  useMutationState
};
//# sourceMappingURL=useMutationState.js.map