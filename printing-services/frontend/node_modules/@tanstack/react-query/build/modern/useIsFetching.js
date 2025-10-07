"use client";

// src/useIsFetching.ts
import * as React from "react";
import { notifyManager } from "@tanstack/query-core";
import { useQueryClient } from "./QueryClientProvider.js";
function useIsFetching(filters, queryClient) {
  const client = useQueryClient(queryClient);
  const queryCache = client.getQueryCache();
  return React.useSyncExternalStore(
    React.useCallback(
      (onStoreChange) => queryCache.subscribe(notifyManager.batchCalls(onStoreChange)),
      [queryCache]
    ),
    () => client.isFetching(filters),
    () => client.isFetching(filters)
  );
}
export {
  useIsFetching
};
//# sourceMappingURL=useIsFetching.js.map