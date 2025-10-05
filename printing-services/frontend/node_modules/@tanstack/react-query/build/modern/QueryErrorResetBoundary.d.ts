import * as react_jsx_runtime from 'react/jsx-runtime';
import * as React from 'react';

type QueryErrorResetFunction = () => void;
type QueryErrorIsResetFunction = () => boolean;
type QueryErrorClearResetFunction = () => void;
interface QueryErrorResetBoundaryValue {
    clearReset: QueryErrorClearResetFunction;
    isReset: QueryErrorIsResetFunction;
    reset: QueryErrorResetFunction;
}
declare const useQueryErrorResetBoundary: () => QueryErrorResetBoundaryValue;
type QueryErrorResetBoundaryFunction = (value: QueryErrorResetBoundaryValue) => React.ReactNode;
interface QueryErrorResetBoundaryProps {
    children: QueryErrorResetBoundaryFunction | React.ReactNode;
}
declare const QueryErrorResetBoundary: ({ children, }: QueryErrorResetBoundaryProps) => react_jsx_runtime.JSX.Element;

export { type QueryErrorClearResetFunction, type QueryErrorIsResetFunction, QueryErrorResetBoundary, type QueryErrorResetBoundaryFunction, type QueryErrorResetBoundaryProps, type QueryErrorResetBoundaryValue, type QueryErrorResetFunction, useQueryErrorResetBoundary };
