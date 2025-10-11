"use client";

// src/useSuspenseInfiniteQuery.ts
import { InfiniteQueryObserver, skipToken } from "@tanstack/query-core";
import { useBaseQuery } from "./useBaseQuery.js";
import { defaultThrowOnError } from "./suspense.js";
function useSuspenseInfiniteQuery(options, queryClient) {
  if (process.env.NODE_ENV !== "production") {
    if (options.queryFn === skipToken) {
      console.error("skipToken is not allowed for useSuspenseInfiniteQuery");
    }
  }
  return useBaseQuery(
    {
      ...options,
      enabled: true,
      suspense: true,
      throwOnError: defaultThrowOnError
    },
    InfiniteQueryObserver,
    queryClient
  );
}
export {
  useSuspenseInfiniteQuery
};
//# sourceMappingURL=useSuspenseInfiniteQuery.js.map