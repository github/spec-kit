import { DefaultError, QueryKey, Query, DefaultedQueryObserverOptions, QueryObserverResult, QueryObserver } from '@tanstack/query-core';
import { QueryErrorResetBoundaryValue } from './QueryErrorResetBoundary.js';
import 'react/jsx-runtime';
import 'react';

declare const defaultThrowOnError: <TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey>(_error: TError, query: Query<TQueryFnData, TError, TData, TQueryKey>) => boolean;
declare const ensureSuspenseTimers: (defaultedOptions: DefaultedQueryObserverOptions<any, any, any, any, any>) => void;
declare const willFetch: (result: QueryObserverResult<any, any>, isRestoring: boolean) => boolean;
declare const shouldSuspend: (defaultedOptions: DefaultedQueryObserverOptions<any, any, any, any, any> | undefined, result: QueryObserverResult<any, any>) => boolean | undefined;
declare const fetchOptimistic: <TQueryFnData, TError, TData, TQueryData, TQueryKey extends QueryKey>(defaultedOptions: DefaultedQueryObserverOptions<TQueryFnData, TError, TData, TQueryData, TQueryKey>, observer: QueryObserver<TQueryFnData, TError, TData, TQueryData, TQueryKey>, errorResetBoundary: QueryErrorResetBoundaryValue) => Promise<void | QueryObserverResult<TData, TError>>;

export { defaultThrowOnError, ensureSuspenseTimers, fetchOptimistic, shouldSuspend, willFetch };
