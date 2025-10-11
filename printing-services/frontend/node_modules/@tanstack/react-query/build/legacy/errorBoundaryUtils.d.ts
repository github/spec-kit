import { QueryKey, DefaultedQueryObserverOptions, QueryObserverResult, ThrowOnError, Query } from '@tanstack/query-core';
import { QueryErrorResetBoundaryValue } from './QueryErrorResetBoundary.js';
import 'react/jsx-runtime';
import 'react';

declare const ensurePreventErrorBoundaryRetry: <TQueryFnData, TError, TData, TQueryData, TQueryKey extends QueryKey>(options: DefaultedQueryObserverOptions<TQueryFnData, TError, TData, TQueryData, TQueryKey>, errorResetBoundary: QueryErrorResetBoundaryValue) => void;
declare const useClearResetErrorBoundary: (errorResetBoundary: QueryErrorResetBoundaryValue) => void;
declare const getHasError: <TData, TError, TQueryFnData, TQueryData, TQueryKey extends QueryKey>({ result, errorResetBoundary, throwOnError, query, suspense, }: {
    result: QueryObserverResult<TData, TError>;
    errorResetBoundary: QueryErrorResetBoundaryValue;
    throwOnError: ThrowOnError<TQueryFnData, TError, TQueryData, TQueryKey>;
    query: Query<TQueryFnData, TError, TQueryData, TQueryKey> | undefined;
    suspense: boolean | undefined;
}) => boolean | undefined;

export { ensurePreventErrorBoundaryRetry, getHasError, useClearResetErrorBoundary };
