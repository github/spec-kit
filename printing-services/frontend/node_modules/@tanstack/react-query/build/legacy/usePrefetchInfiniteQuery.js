// src/usePrefetchInfiniteQuery.tsx
import { useQueryClient } from "./QueryClientProvider.js";
function usePrefetchInfiniteQuery(options, queryClient) {
  const client = useQueryClient(queryClient);
  if (!client.getQueryState(options.queryKey)) {
    client.prefetchInfiniteQuery(options);
  }
}
export {
  usePrefetchInfiniteQuery
};
//# sourceMappingURL=usePrefetchInfiniteQuery.js.map