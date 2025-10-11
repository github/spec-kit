import { useQueryClient } from './QueryClientProvider'
import type { DefaultError, QueryClient, QueryKey } from '@tanstack/query-core'
import type { UsePrefetchQueryOptions } from './types'

export function usePrefetchQuery<
  TQueryFnData = unknown,
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
>(
  options: UsePrefetchQueryOptions<TQueryFnData, TError, TData, TQueryKey>,
  queryClient?: QueryClient,
) {
  const client = useQueryClient(queryClient)

  if (!client.getQueryState(options.queryKey)) {
    client.prefetchQuery(options)
  }
}
