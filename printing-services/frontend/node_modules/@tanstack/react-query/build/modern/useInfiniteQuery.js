"use client";

// src/useInfiniteQuery.ts
import { InfiniteQueryObserver } from "@tanstack/query-core";
import { useBaseQuery } from "./useBaseQuery.js";
function useInfiniteQuery(options, queryClient) {
  return useBaseQuery(
    options,
    InfiniteQueryObserver,
    queryClient
  );
}
export {
  useInfiniteQuery
};
//# sourceMappingURL=useInfiniteQuery.js.map