import { UseSuspenseQueryOptions, UseSuspenseQueryResult } from './types.js';
import { DefaultError, QueryKey, QueryClient } from '@tanstack/query-core';

declare function useSuspenseQuery<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey>(options: UseSuspenseQueryOptions<TQueryFnData, TError, TData, TQueryKey>, queryClient?: QueryClient): UseSuspenseQueryResult<TData, TError>;

export { useSuspenseQuery };
