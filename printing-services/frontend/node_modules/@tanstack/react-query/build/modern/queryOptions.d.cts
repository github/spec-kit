import { DefaultError, QueryKey, NonUndefinedGuard, QueryFunction, InitialDataFunction, DataTag, OmitKeyof, SkipToken } from '@tanstack/query-core';
import { UseQueryOptions } from './types.cjs';

type UndefinedInitialDataOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey> = UseQueryOptions<TQueryFnData, TError, TData, TQueryKey> & {
    initialData?: undefined | InitialDataFunction<NonUndefinedGuard<TQueryFnData>> | NonUndefinedGuard<TQueryFnData>;
};
type UnusedSkipTokenOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey> = OmitKeyof<UseQueryOptions<TQueryFnData, TError, TData, TQueryKey>, 'queryFn'> & {
    queryFn?: Exclude<UseQueryOptions<TQueryFnData, TError, TData, TQueryKey>['queryFn'], SkipToken | undefined>;
};
type DefinedInitialDataOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey> = Omit<UseQueryOptions<TQueryFnData, TError, TData, TQueryKey>, 'queryFn'> & {
    initialData: NonUndefinedGuard<TQueryFnData> | (() => NonUndefinedGuard<TQueryFnData>);
    queryFn?: QueryFunction<TQueryFnData, TQueryKey>;
};
declare function queryOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey>(options: DefinedInitialDataOptions<TQueryFnData, TError, TData, TQueryKey>): DefinedInitialDataOptions<TQueryFnData, TError, TData, TQueryKey> & {
    queryKey: DataTag<TQueryKey, TQueryFnData, TError>;
};
declare function queryOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey>(options: UnusedSkipTokenOptions<TQueryFnData, TError, TData, TQueryKey>): UnusedSkipTokenOptions<TQueryFnData, TError, TData, TQueryKey> & {
    queryKey: DataTag<TQueryKey, TQueryFnData, TError>;
};
declare function queryOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey>(options: UndefinedInitialDataOptions<TQueryFnData, TError, TData, TQueryKey>): UndefinedInitialDataOptions<TQueryFnData, TError, TData, TQueryKey> & {
    queryKey: DataTag<TQueryKey, TQueryFnData, TError>;
};

export { type DefinedInitialDataOptions, type UndefinedInitialDataOptions, type UnusedSkipTokenOptions, queryOptions };
