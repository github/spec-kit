import { DefaultError, QueryObserverResult, DefinedQueryObserverResult, QueryKey, OmitKeyof, QueryObserverOptions, SkipToken, DistributiveOmit, InfiniteQueryObserverOptions, DefinedInfiniteQueryObserverResult, FetchQueryOptions, MutationObserverOptions, Override, MutationObserverResult, MutateFunction, InfiniteQueryObserverResult } from '@tanstack/query-core';

type AnyUseBaseQueryOptions = UseBaseQueryOptions<any, any, any, any, any>;
interface UseBaseQueryOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryData = TQueryFnData, TQueryKey extends QueryKey = QueryKey> extends QueryObserverOptions<TQueryFnData, TError, TData, TQueryData, TQueryKey> {
    /**
     * Set this to `false` to unsubscribe this observer from updates to the query cache.
     * Defaults to `true`.
     */
    subscribed?: boolean;
}
interface UsePrefetchQueryOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey> extends OmitKeyof<FetchQueryOptions<TQueryFnData, TError, TData, TQueryKey>, 'queryFn'> {
    queryFn?: Exclude<FetchQueryOptions<TQueryFnData, TError, TData, TQueryKey>['queryFn'], SkipToken>;
}
type AnyUseQueryOptions = UseQueryOptions<any, any, any, any>;
interface UseQueryOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey> extends OmitKeyof<UseBaseQueryOptions<TQueryFnData, TError, TData, TQueryFnData, TQueryKey>, 'suspense'> {
}
type AnyUseSuspenseQueryOptions = UseSuspenseQueryOptions<any, any, any, any>;
interface UseSuspenseQueryOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey> extends OmitKeyof<UseQueryOptions<TQueryFnData, TError, TData, TQueryKey>, 'queryFn' | 'enabled' | 'throwOnError' | 'placeholderData'> {
    queryFn?: Exclude<UseQueryOptions<TQueryFnData, TError, TData, TQueryKey>['queryFn'], SkipToken>;
}
type AnyUseInfiniteQueryOptions = UseInfiniteQueryOptions<any, any, any, any, any>;
interface UseInfiniteQueryOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey, TPageParam = unknown> extends OmitKeyof<InfiniteQueryObserverOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam>, 'suspense'> {
    /**
     * Set this to `false` to unsubscribe this observer from updates to the query cache.
     * Defaults to `true`.
     */
    subscribed?: boolean;
}
type AnyUseSuspenseInfiniteQueryOptions = UseSuspenseInfiniteQueryOptions<any, any, any, any, any>;
interface UseSuspenseInfiniteQueryOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey, TPageParam = unknown> extends OmitKeyof<UseInfiniteQueryOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam>, 'queryFn' | 'enabled' | 'throwOnError' | 'placeholderData'> {
    queryFn?: Exclude<UseInfiniteQueryOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam>['queryFn'], SkipToken>;
}
type UseBaseQueryResult<TData = unknown, TError = DefaultError> = QueryObserverResult<TData, TError>;
type UseQueryResult<TData = unknown, TError = DefaultError> = UseBaseQueryResult<TData, TError>;
type UseSuspenseQueryResult<TData = unknown, TError = DefaultError> = DistributiveOmit<DefinedQueryObserverResult<TData, TError>, 'isPlaceholderData' | 'promise'>;
type DefinedUseQueryResult<TData = unknown, TError = DefaultError> = DefinedQueryObserverResult<TData, TError>;
type UseInfiniteQueryResult<TData = unknown, TError = DefaultError> = InfiniteQueryObserverResult<TData, TError>;
type DefinedUseInfiniteQueryResult<TData = unknown, TError = DefaultError> = DefinedInfiniteQueryObserverResult<TData, TError>;
type UseSuspenseInfiniteQueryResult<TData = unknown, TError = DefaultError> = OmitKeyof<DefinedInfiniteQueryObserverResult<TData, TError>, 'isPlaceholderData' | 'promise'>;
type AnyUseMutationOptions = UseMutationOptions<any, any, any, any>;
interface UseMutationOptions<TData = unknown, TError = DefaultError, TVariables = void, TOnMutateResult = unknown> extends OmitKeyof<MutationObserverOptions<TData, TError, TVariables, TOnMutateResult>, '_defaulted'> {
}
type UseMutateFunction<TData = unknown, TError = DefaultError, TVariables = void, TOnMutateResult = unknown> = (...args: Parameters<MutateFunction<TData, TError, TVariables, TOnMutateResult>>) => void;
type UseMutateAsyncFunction<TData = unknown, TError = DefaultError, TVariables = void, TOnMutateResult = unknown> = MutateFunction<TData, TError, TVariables, TOnMutateResult>;
type UseBaseMutationResult<TData = unknown, TError = DefaultError, TVariables = unknown, TOnMutateResult = unknown> = Override<MutationObserverResult<TData, TError, TVariables, TOnMutateResult>, {
    mutate: UseMutateFunction<TData, TError, TVariables, TOnMutateResult>;
}> & {
    mutateAsync: UseMutateAsyncFunction<TData, TError, TVariables, TOnMutateResult>;
};
type UseMutationResult<TData = unknown, TError = DefaultError, TVariables = unknown, TOnMutateResult = unknown> = UseBaseMutationResult<TData, TError, TVariables, TOnMutateResult>;

export type { AnyUseBaseQueryOptions, AnyUseInfiniteQueryOptions, AnyUseMutationOptions, AnyUseQueryOptions, AnyUseSuspenseInfiniteQueryOptions, AnyUseSuspenseQueryOptions, DefinedUseInfiniteQueryResult, DefinedUseQueryResult, UseBaseMutationResult, UseBaseQueryOptions, UseBaseQueryResult, UseInfiniteQueryOptions, UseInfiniteQueryResult, UseMutateAsyncFunction, UseMutateFunction, UseMutationOptions, UseMutationResult, UsePrefetchQueryOptions, UseQueryOptions, UseQueryResult, UseSuspenseInfiniteQueryOptions, UseSuspenseInfiniteQueryResult, UseSuspenseQueryOptions, UseSuspenseQueryResult };
