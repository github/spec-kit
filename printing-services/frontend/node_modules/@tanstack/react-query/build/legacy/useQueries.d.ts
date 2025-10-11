import { UseQueryResult, DefinedUseQueryResult, UseQueryOptions } from './types.js';
import { QueryFunction, ThrowOnError, DefaultError, QueryKey, OmitKeyof, QueriesPlaceholderDataFunction, QueryClient } from '@tanstack/query-core';

type UseQueryOptionsForUseQueries<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey> = OmitKeyof<UseQueryOptions<TQueryFnData, TError, TData, TQueryKey>, 'placeholderData' | 'subscribed'> & {
    placeholderData?: TQueryFnData | QueriesPlaceholderDataFunction<TQueryFnData>;
};
type MAXIMUM_DEPTH = 20;
type SkipTokenForUseQueries = symbol;
type GetUseQueryOptionsForUseQueries<T> = T extends {
    queryFnData: infer TQueryFnData;
    error?: infer TError;
    data: infer TData;
} ? UseQueryOptionsForUseQueries<TQueryFnData, TError, TData> : T extends {
    queryFnData: infer TQueryFnData;
    error?: infer TError;
} ? UseQueryOptionsForUseQueries<TQueryFnData, TError> : T extends {
    data: infer TData;
    error?: infer TError;
} ? UseQueryOptionsForUseQueries<unknown, TError, TData> : T extends [infer TQueryFnData, infer TError, infer TData] ? UseQueryOptionsForUseQueries<TQueryFnData, TError, TData> : T extends [infer TQueryFnData, infer TError] ? UseQueryOptionsForUseQueries<TQueryFnData, TError> : T extends [infer TQueryFnData] ? UseQueryOptionsForUseQueries<TQueryFnData> : T extends {
    queryFn?: QueryFunction<infer TQueryFnData, infer TQueryKey> | SkipTokenForUseQueries;
    select?: (data: any) => infer TData;
    throwOnError?: ThrowOnError<any, infer TError, any, any>;
} ? UseQueryOptionsForUseQueries<TQueryFnData, unknown extends TError ? DefaultError : TError, unknown extends TData ? TQueryFnData : TData, TQueryKey> : UseQueryOptionsForUseQueries;
type GetDefinedOrUndefinedQueryResult<T, TData, TError = unknown> = T extends {
    initialData?: infer TInitialData;
} ? unknown extends TInitialData ? UseQueryResult<TData, TError> : TInitialData extends TData ? DefinedUseQueryResult<TData, TError> : TInitialData extends () => infer TInitialDataResult ? unknown extends TInitialDataResult ? UseQueryResult<TData, TError> : TInitialDataResult extends TData ? DefinedUseQueryResult<TData, TError> : UseQueryResult<TData, TError> : UseQueryResult<TData, TError> : UseQueryResult<TData, TError>;
type GetUseQueryResult<T> = T extends {
    queryFnData: any;
    error?: infer TError;
    data: infer TData;
} ? GetDefinedOrUndefinedQueryResult<T, TData, TError> : T extends {
    queryFnData: infer TQueryFnData;
    error?: infer TError;
} ? GetDefinedOrUndefinedQueryResult<T, TQueryFnData, TError> : T extends {
    data: infer TData;
    error?: infer TError;
} ? GetDefinedOrUndefinedQueryResult<T, TData, TError> : T extends [any, infer TError, infer TData] ? GetDefinedOrUndefinedQueryResult<T, TData, TError> : T extends [infer TQueryFnData, infer TError] ? GetDefinedOrUndefinedQueryResult<T, TQueryFnData, TError> : T extends [infer TQueryFnData] ? GetDefinedOrUndefinedQueryResult<T, TQueryFnData> : T extends {
    queryFn?: QueryFunction<infer TQueryFnData, any> | SkipTokenForUseQueries;
    select?: (data: any) => infer TData;
    throwOnError?: ThrowOnError<any, infer TError, any, any>;
} ? GetDefinedOrUndefinedQueryResult<T, unknown extends TData ? TQueryFnData : TData, unknown extends TError ? DefaultError : TError> : UseQueryResult;
/**
 * QueriesOptions reducer recursively unwraps function arguments to infer/enforce type param
 */
type QueriesOptions<T extends Array<any>, TResults extends Array<any> = [], TDepth extends ReadonlyArray<number> = []> = TDepth['length'] extends MAXIMUM_DEPTH ? Array<UseQueryOptionsForUseQueries> : T extends [] ? [] : T extends [infer Head] ? [...TResults, GetUseQueryOptionsForUseQueries<Head>] : T extends [infer Head, ...infer Tails] ? QueriesOptions<[
    ...Tails
], [
    ...TResults,
    GetUseQueryOptionsForUseQueries<Head>
], [
    ...TDepth,
    1
]> : ReadonlyArray<unknown> extends T ? T : T extends Array<UseQueryOptionsForUseQueries<infer TQueryFnData, infer TError, infer TData, infer TQueryKey>> ? Array<UseQueryOptionsForUseQueries<TQueryFnData, TError, TData, TQueryKey>> : Array<UseQueryOptionsForUseQueries>;
/**
 * QueriesResults reducer recursively maps type param to results
 */
type QueriesResults<T extends Array<any>, TResults extends Array<any> = [], TDepth extends ReadonlyArray<number> = []> = TDepth['length'] extends MAXIMUM_DEPTH ? Array<UseQueryResult> : T extends [] ? [] : T extends [infer Head] ? [...TResults, GetUseQueryResult<Head>] : T extends [infer Head, ...infer Tails] ? QueriesResults<[
    ...Tails
], [
    ...TResults,
    GetUseQueryResult<Head>
], [
    ...TDepth,
    1
]> : {
    [K in keyof T]: GetUseQueryResult<T[K]>;
};
declare function useQueries<T extends Array<any>, TCombinedResult = QueriesResults<T>>({ queries, ...options }: {
    queries: readonly [...QueriesOptions<T>] | readonly [...{
        [K in keyof T]: GetUseQueryOptionsForUseQueries<T[K]>;
    }];
    combine?: (result: QueriesResults<T>) => TCombinedResult;
    subscribed?: boolean;
}, queryClient?: QueryClient): TCombinedResult;

export { type QueriesOptions, type QueriesResults, useQueries };
