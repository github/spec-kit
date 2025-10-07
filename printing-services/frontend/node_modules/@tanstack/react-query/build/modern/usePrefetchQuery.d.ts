import { DefaultError, QueryKey, QueryClient } from '@tanstack/query-core';
import { UsePrefetchQueryOptions } from './types.js';

declare function usePrefetchQuery<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey>(options: UsePrefetchQueryOptions<TQueryFnData, TError, TData, TQueryKey>, queryClient?: QueryClient): void;

export { usePrefetchQuery };
