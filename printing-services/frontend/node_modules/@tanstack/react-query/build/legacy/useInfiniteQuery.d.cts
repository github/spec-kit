import { DefaultError, InfiniteData, QueryKey, QueryClient } from '@tanstack/query-core';
import { DefinedUseInfiniteQueryResult, UseInfiniteQueryResult, UseInfiniteQueryOptions } from './types.cjs';
import { DefinedInitialDataInfiniteOptions, UndefinedInitialDataInfiniteOptions } from './infiniteQueryOptions.cjs';

declare function useInfiniteQuery<TQueryFnData, TError = DefaultError, TData = InfiniteData<TQueryFnData>, TQueryKey extends QueryKey = QueryKey, TPageParam = unknown>(options: DefinedInitialDataInfiniteOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam>, queryClient?: QueryClient): DefinedUseInfiniteQueryResult<TData, TError>;
declare function useInfiniteQuery<TQueryFnData, TError = DefaultError, TData = InfiniteData<TQueryFnData>, TQueryKey extends QueryKey = QueryKey, TPageParam = unknown>(options: UndefinedInitialDataInfiniteOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam>, queryClient?: QueryClient): UseInfiniteQueryResult<TData, TError>;
declare function useInfiniteQuery<TQueryFnData, TError = DefaultError, TData = InfiniteData<TQueryFnData>, TQueryKey extends QueryKey = QueryKey, TPageParam = unknown>(options: UseInfiniteQueryOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam>, queryClient?: QueryClient): UseInfiniteQueryResult<TData, TError>;

export { useInfiniteQuery };
