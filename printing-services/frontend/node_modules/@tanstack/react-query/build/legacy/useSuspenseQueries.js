"use client";

// src/useSuspenseQueries.ts
import { skipToken } from "@tanstack/query-core";
import { useQueries } from "./useQueries.js";
import { defaultThrowOnError } from "./suspense.js";
function useSuspenseQueries(options, queryClient) {
  return useQueries(
    {
      ...options,
      queries: options.queries.map((query) => {
        if (process.env.NODE_ENV !== "production") {
          if (query.queryFn === skipToken) {
            console.error("skipToken is not allowed for useSuspenseQueries");
          }
        }
        return {
          ...query,
          suspense: true,
          throwOnError: defaultThrowOnError,
          enabled: true,
          placeholderData: void 0
        };
      })
    },
    queryClient
  );
}
export {
  useSuspenseQueries
};
//# sourceMappingURL=useSuspenseQueries.js.map