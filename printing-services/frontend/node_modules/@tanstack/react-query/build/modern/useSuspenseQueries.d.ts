import { UseSuspenseQueryResult, UseSuspenseQueryOptions } from './types.js';
import { QueryFunction, ThrowOnError, DefaultError, QueryClient } from '@tanstack/query-core';

type MAXIMUM_DEPTH = 20;
type SkipTokenForUseQueries = symbol;
type GetUseSuspenseQueryOptions<T> = T extends {
    queryFnData: infer TQueryFnData;
    error?: infer TError;
    data: infer TData;
} ? UseSuspenseQueryOptions<TQueryFnData, TError, TData> : T extends {
    queryFnData: infer TQueryFnData;
    error?: infer TError;
} ? UseSuspenseQueryOptions<TQueryFnData, TError> : T extends {
    data: infer TData;
    error?: infer TError;
} ? UseSuspenseQueryOptions<unknown, TError, TData> : T extends [infer TQueryFnData, infer TError, infer TData] ? UseSuspenseQueryOptions<TQueryFnData, TError, TData> : T extends [infer TQueryFnData, infer TError] ? UseSuspenseQueryOptions<TQueryFnData, TError> : T extends [infer TQueryFnData] ? UseSuspenseQueryOptions<TQueryFnData> : T extends {
    queryFn?: QueryFunction<infer TQueryFnData, infer TQueryKey> | SkipTokenForUseQueries;
    select?: (data: any) => infer TData;
    throwOnError?: ThrowOnError<any, infer TError, any, any>;
} ? UseSuspenseQueryOptions<TQueryFnData, TError, TData, TQueryKey> : T extends {
    queryFn?: QueryFunction<infer TQueryFnData, infer TQueryKey> | SkipTokenForUseQueries;
    throwOnError?: ThrowOnError<any, infer TError, any, any>;
} ? UseSuspenseQueryOptions<TQueryFnData, TError, TQueryFnData, TQueryKey> : UseSuspenseQueryOptions;
type GetUseSuspenseQueryResult<T> = T extends {
    queryFnData: any;
    error?: infer TError;
    data: infer TData;
} ? UseSuspenseQueryResult<TData, TError> : T extends {
    queryFnData: infer TQueryFnData;
    error?: infer TError;
} ? UseSuspenseQueryResult<TQueryFnData, TError> : T extends {
    data: infer TData;
    error?: infer TError;
} ? UseSuspenseQueryResult<TData, TError> : T extends [any, infer TError, infer TData] ? UseSuspenseQueryResult<TData, TError> : T extends [infer TQueryFnData, infer TError] ? UseSuspenseQueryResult<TQueryFnData, TError> : T extends [infer TQueryFnData] ? UseSuspenseQueryResult<TQueryFnData> : T extends {
    queryFn?: QueryFunction<infer TQueryFnData, any> | SkipTokenForUseQueries;
    select?: (data: any) => infer TData;
    throwOnError?: ThrowOnError<any, infer TError, any, any>;
} ? UseSuspenseQueryResult<unknown extends TData ? TQueryFnData : TData, unknown extends TError ? DefaultError : TError> : T extends {
    queryFn?: QueryFunction<infer TQueryFnData, any> | SkipTokenForUseQueries;
    throwOnError?: ThrowOnError<any, infer TError, any, any>;
} ? UseSuspenseQueryResult<TQueryFnData, unknown extends TError ? DefaultError : TError> : UseSuspenseQueryResult;
/**
 * SuspenseQueriesOptions reducer recursively unwraps function arguments to infer/enforce type param
 */
type SuspenseQueriesOptions<T extends Array<any>, TResults extends Array<any> = [], TDepth extends ReadonlyArray<number> = []> = TDepth['length'] extends MAXIMUM_DEPTH ? Array<UseSuspenseQueryOptions> : T extends [] ? [] : T extends [infer Head] ? [...TResults, GetUseSuspenseQueryOptions<Head>] : T extends [infer Head, ...infer Tails] ? SuspenseQueriesOptions<[
    ...Tails
], [
    ...TResults,
    GetUseSuspenseQueryOptions<Head>
], [
    ...TDepth,
    1
]> : Array<unknown> extends T ? T : T extends Array<UseSuspenseQueryOptions<infer TQueryFnData, infer TError, infer TData, infer TQueryKey>> ? Array<UseSuspenseQueryOptions<TQueryFnData, TError, TData, TQueryKey>> : Array<UseSuspenseQueryOptions>;
/**
 * SuspenseQueriesResults reducer recursively maps type param to results
 */
type SuspenseQueriesResults<T extends Array<any>, TResults extends Array<any> = [], TDepth extends ReadonlyArray<number> = []> = TDepth['length'] extends MAXIMUM_DEPTH ? Array<UseSuspenseQueryResult> : T extends [] ? [] : T extends [infer Head] ? [...TResults, GetUseSuspenseQueryResult<Head>] : T extends [infer Head, ...infer Tails] ? SuspenseQueriesResults<[
    ...Tails
], [
    ...TResults,
    GetUseSuspenseQueryResult<Head>
], [
    ...TDepth,
    1
]> : {
    [K in keyof T]: GetUseSuspenseQueryResult<T[K]>;
};
declare function useSuspenseQueries<T extends Array<any>, TCombinedResult = SuspenseQueriesResults<T>>(options: {
    queries: readonly [...SuspenseQueriesOptions<T>] | readonly [...{
        [K in keyof T]: GetUseSuspenseQueryOptions<T[K]>;
    }];
    combine?: (result: SuspenseQueriesResults<T>) => TCombinedResult;
}, queryClient?: QueryClient): TCombinedResult;
declare function useSuspenseQueries<T extends Array<any>, TCombinedResult = SuspenseQueriesResults<T>>(options: {
    queries: readonly [...SuspenseQueriesOptions<T>];
    combine?: (result: SuspenseQueriesResults<T>) => TCombinedResult;
}, queryClient?: QueryClient): TCombinedResult;

export { type SuspenseQueriesOptions, type SuspenseQueriesResults, useSuspenseQueries };
