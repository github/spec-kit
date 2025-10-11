'use client'
import { InfiniteQueryObserver, skipToken } from '@tanstack/query-core'
import { useBaseQuery } from './useBaseQuery'
import { defaultThrowOnError } from './suspense'
import type {
  DefaultError,
  InfiniteData,
  InfiniteQueryObserverSuccessResult,
  QueryClient,
  QueryKey,
  QueryObserver,
} from '@tanstack/query-core'
import type {
  UseSuspenseInfiniteQueryOptions,
  UseSuspenseInfiniteQueryResult,
} from './types'

export function useSuspenseInfiniteQuery<
  TQueryFnData,
  TError = DefaultError,
  TData = InfiniteData<TQueryFnData>,
  TQueryKey extends QueryKey = QueryKey,
  TPageParam = unknown,
>(
  options: UseSuspenseInfiniteQueryOptions<
    TQueryFnData,
    TError,
    TData,
    TQueryKey,
    TPageParam
  >,
  queryClient?: QueryClient,
): UseSuspenseInfiniteQueryResult<TData, TError> {
  if (process.env.NODE_ENV !== 'production') {
    if ((options.queryFn as any) === skipToken) {
      console.error('skipToken is not allowed for useSuspenseInfiniteQuery')
    }
  }

  return useBaseQuery(
    {
      ...options,
      enabled: true,
      suspense: true,
      throwOnError: defaultThrowOnError,
    },
    InfiniteQueryObserver as typeof QueryObserver,
    queryClient,
  ) as InfiniteQueryObserverSuccessResult<TData, TError>
}
