"use client";

// src/useQuery.ts
import { QueryObserver } from "@tanstack/query-core";
import { useBaseQuery } from "./useBaseQuery.js";
function useQuery(options, queryClient) {
  return useBaseQuery(options, QueryObserver, queryClient);
}
export {
  useQuery
};
//# sourceMappingURL=useQuery.js.map