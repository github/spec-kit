// src/usePrefetchQuery.tsx
import { useQueryClient } from "./QueryClientProvider.js";
function usePrefetchQuery(options, queryClient) {
  const client = useQueryClient(queryClient);
  if (!client.getQueryState(options.queryKey)) {
    client.prefetchQuery(options);
  }
}
export {
  usePrefetchQuery
};
//# sourceMappingURL=usePrefetchQuery.js.map