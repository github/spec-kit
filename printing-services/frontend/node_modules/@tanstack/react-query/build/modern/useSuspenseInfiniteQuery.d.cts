import { DefaultError, InfiniteData, QueryKey, QueryClient } from '@tanstack/query-core';
import { UseSuspenseInfiniteQueryOptions, UseSuspenseInfiniteQueryResult } from './types.cjs';

declare function useSuspenseInfiniteQuery<TQueryFnData, TError = DefaultError, TData = InfiniteData<TQueryFnData>, TQueryKey extends QueryKey = QueryKey, TPageParam = unknown>(options: UseSuspenseInfiniteQueryOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam>, queryClient?: QueryClient): UseSuspenseInfiniteQueryResult<TData, TError>;

export { useSuspenseInfiniteQuery };
