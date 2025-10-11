import { useQueryClient } from './QueryClientProvider'
import type {
  DefaultError,
  FetchInfiniteQueryOptions,
  QueryClient,
  QueryKey,
} from '@tanstack/query-core'

export function usePrefetchInfiniteQuery<
  TQueryFnData = unknown,
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
  TPageParam = unknown,
>(
  options: FetchInfiniteQueryOptions<
    TQueryFnData,
    TError,
    TData,
    TQueryKey,
    TPageParam
  >,
  queryClient?: QueryClient,
) {
  const client = useQueryClient(queryClient)

  if (!client.getQueryState(options.queryKey)) {
    client.prefetchInfiniteQuery(options)
  }
}
