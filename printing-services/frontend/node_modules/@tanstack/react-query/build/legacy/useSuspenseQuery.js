"use client";

// src/useSuspenseQuery.ts
import { QueryObserver, skipToken } from "@tanstack/query-core";
import { useBaseQuery } from "./useBaseQuery.js";
import { defaultThrowOnError } from "./suspense.js";
function useSuspenseQuery(options, queryClient) {
  if (process.env.NODE_ENV !== "production") {
    if (options.queryFn === skipToken) {
      console.error("skipToken is not allowed for useSuspenseQuery");
    }
  }
  return useBaseQuery(
    {
      ...options,
      enabled: true,
      suspense: true,
      throwOnError: defaultThrowOnError,
      placeholderData: void 0
    },
    QueryObserver,
    queryClient
  );
}
export {
  useSuspenseQuery
};
//# sourceMappingURL=useSuspenseQuery.js.map