'use client'
import * as React from 'react'

import {
  QueriesObserver,
  QueryObserver,
  noop,
  notifyManager,
} from '@tanstack/query-core'
import { useQueryClient } from './QueryClientProvider'
import { useIsRestoring } from './IsRestoringProvider'
import { useQueryErrorResetBoundary } from './QueryErrorResetBoundary'
import {
  ensurePreventErrorBoundaryRetry,
  getHasError,
  useClearResetErrorBoundary,
} from './errorBoundaryUtils'
import {
  ensureSuspenseTimers,
  fetchOptimistic,
  shouldSuspend,
  willFetch,
} from './suspense'
import type {
  DefinedUseQueryResult,
  UseQueryOptions,
  UseQueryResult,
} from './types'
import type {
  DefaultError,
  OmitKeyof,
  QueriesObserverOptions,
  QueriesPlaceholderDataFunction,
  QueryClient,
  QueryFunction,
  QueryKey,
  QueryObserverOptions,
  ThrowOnError,
} from '@tanstack/query-core'

// This defines the `UseQueryOptions` that are accepted in `QueriesOptions` & `GetOptions`.
// `placeholderData` function always gets undefined passed
type UseQueryOptionsForUseQueries<
  TQueryFnData = unknown,
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
> = OmitKeyof<
  UseQueryOptions<TQueryFnData, TError, TData, TQueryKey>,
  'placeholderData' | 'subscribed'
> & {
  placeholderData?: TQueryFnData | QueriesPlaceholderDataFunction<TQueryFnData>
}

// Avoid TS depth-limit error in case of large array literal
type MAXIMUM_DEPTH = 20

// Widen the type of the symbol to enable type inference even if skipToken is not immutable.
type SkipTokenForUseQueries = symbol

type GetUseQueryOptionsForUseQueries<T> =
  // Part 1: responsible for applying explicit type parameter to function arguments, if object { queryFnData: TQueryFnData, error: TError, data: TData }
  T extends {
    queryFnData: infer TQueryFnData
    error?: infer TError
    data: infer TData
  }
    ? UseQueryOptionsForUseQueries<TQueryFnData, TError, TData>
    : T extends { queryFnData: infer TQueryFnData; error?: infer TError }
      ? UseQueryOptionsForUseQueries<TQueryFnData, TError>
      : T extends { data: infer TData; error?: infer TError }
        ? UseQueryOptionsForUseQueries<unknown, TError, TData>
        : // Part 2: responsible for applying explicit type parameter to function arguments, if tuple [TQueryFnData, TError, TData]
          T extends [infer TQueryFnData, infer TError, infer TData]
          ? UseQueryOptionsForUseQueries<TQueryFnData, TError, TData>
          : T extends [infer TQueryFnData, infer TError]
            ? UseQueryOptionsForUseQueries<TQueryFnData, TError>
            : T extends [infer TQueryFnData]
              ? UseQueryOptionsForUseQueries<TQueryFnData>
              : // Part 3: responsible for inferring and enforcing type if no explicit parameter was provided
                T extends {
                    queryFn?:
                      | QueryFunction<infer TQueryFnData, infer TQueryKey>
                      | SkipTokenForUseQueries
                    select?: (data: any) => infer TData
                    throwOnError?: ThrowOnError<any, infer TError, any, any>
                  }
                ? UseQueryOptionsForUseQueries<
                    TQueryFnData,
                    unknown extends TError ? DefaultError : TError,
                    unknown extends TData ? TQueryFnData : TData,
                    TQueryKey
                  >
                : // Fallback
                  UseQueryOptionsForUseQueries

// A defined initialData setting should return a DefinedUseQueryResult rather than UseQueryResult
type GetDefinedOrUndefinedQueryResult<T, TData, TError = unknown> = T extends {
  initialData?: infer TInitialData
}
  ? unknown extends TInitialData
    ? UseQueryResult<TData, TError>
    : TInitialData extends TData
      ? DefinedUseQueryResult<TData, TError>
      : TInitialData extends () => infer TInitialDataResult
        ? unknown extends TInitialDataResult
          ? UseQueryResult<TData, TError>
          : TInitialDataResult extends TData
            ? DefinedUseQueryResult<TData, TError>
            : UseQueryResult<TData, TError>
        : UseQueryResult<TData, TError>
  : UseQueryResult<TData, TError>

type GetUseQueryResult<T> =
  // Part 1: responsible for mapping explicit type parameter to function result, if object
  T extends { queryFnData: any; error?: infer TError; data: infer TData }
    ? GetDefinedOrUndefinedQueryResult<T, TData, TError>
    : T extends { queryFnData: infer TQueryFnData; error?: infer TError }
      ? GetDefinedOrUndefinedQueryResult<T, TQueryFnData, TError>
      : T extends { data: infer TData; error?: infer TError }
        ? GetDefinedOrUndefinedQueryResult<T, TData, TError>
        : // Part 2: responsible for mapping explicit type parameter to function result, if tuple
          T extends [any, infer TError, infer TData]
          ? GetDefinedOrUndefinedQueryResult<T, TData, TError>
          : T extends [infer TQueryFnData, infer TError]
            ? GetDefinedOrUndefinedQueryResult<T, TQueryFnData, TError>
            : T extends [infer TQueryFnData]
              ? GetDefinedOrUndefinedQueryResult<T, TQueryFnData>
              : // Part 3: responsible for mapping inferred type to results, if no explicit parameter was provided
                T extends {
                    queryFn?:
                      | QueryFunction<infer TQueryFnData, any>
                      | SkipTokenForUseQueries
                    select?: (data: any) => infer TData
                    throwOnError?: ThrowOnError<any, infer TError, any, any>
                  }
                ? GetDefinedOrUndefinedQueryResult<
                    T,
                    unknown extends TData ? TQueryFnData : TData,
                    unknown extends TError ? DefaultError : TError
                  >
                : // Fallback
                  UseQueryResult

/**
 * QueriesOptions reducer recursively unwraps function arguments to infer/enforce type param
 */
export type QueriesOptions<
  T extends Array<any>,
  TResults extends Array<any> = [],
  TDepth extends ReadonlyArray<number> = [],
> = TDepth['length'] extends MAXIMUM_DEPTH
  ? Array<UseQueryOptionsForUseQueries>
  : T extends []
    ? []
    : T extends [infer Head]
      ? [...TResults, GetUseQueryOptionsForUseQueries<Head>]
      : T extends [infer Head, ...infer Tails]
        ? QueriesOptions<
            [...Tails],
            [...TResults, GetUseQueryOptionsForUseQueries<Head>],
            [...TDepth, 1]
          >
        : ReadonlyArray<unknown> extends T
          ? T
          : // If T is *some* array but we couldn't assign unknown[] to it, then it must hold some known/homogenous type!
            // use this to infer the param types in the case of Array.map() argument
            T extends Array<
                UseQueryOptionsForUseQueries<
                  infer TQueryFnData,
                  infer TError,
                  infer TData,
                  infer TQueryKey
                >
              >
            ? Array<
                UseQueryOptionsForUseQueries<
                  TQueryFnData,
                  TError,
                  TData,
                  TQueryKey
                >
              >
            : // Fallback
              Array<UseQueryOptionsForUseQueries>

/**
 * QueriesResults reducer recursively maps type param to results
 */
export type QueriesResults<
  T extends Array<any>,
  TResults extends Array<any> = [],
  TDepth extends ReadonlyArray<number> = [],
> = TDepth['length'] extends MAXIMUM_DEPTH
  ? Array<UseQueryResult>
  : T extends []
    ? []
    : T extends [infer Head]
      ? [...TResults, GetUseQueryResult<Head>]
      : T extends [infer Head, ...infer Tails]
        ? QueriesResults<
            [...Tails],
            [...TResults, GetUseQueryResult<Head>],
            [...TDepth, 1]
          >
        : { [K in keyof T]: GetUseQueryResult<T[K]> }

export function useQueries<
  T extends Array<any>,
  TCombinedResult = QueriesResults<T>,
>(
  {
    queries,
    ...options
  }: {
    queries:
      | readonly [...QueriesOptions<T>]
      | readonly [...{ [K in keyof T]: GetUseQueryOptionsForUseQueries<T[K]> }]
    combine?: (result: QueriesResults<T>) => TCombinedResult
    subscribed?: boolean
  },
  queryClient?: QueryClient,
): TCombinedResult {
  const client = useQueryClient(queryClient)
  const isRestoring = useIsRestoring()
  const errorResetBoundary = useQueryErrorResetBoundary()

  const defaultedQueries = React.useMemo(
    () =>
      queries.map((opts) => {
        const defaultedOptions = client.defaultQueryOptions(
          opts as QueryObserverOptions,
        )

        // Make sure the results are already in fetching state before subscribing or updating options
        defaultedOptions._optimisticResults = isRestoring
          ? 'isRestoring'
          : 'optimistic'

        return defaultedOptions
      }),
    [queries, client, isRestoring],
  )

  defaultedQueries.forEach((query) => {
    ensureSuspenseTimers(query)
    ensurePreventErrorBoundaryRetry(query, errorResetBoundary)
  })

  useClearResetErrorBoundary(errorResetBoundary)

  const [observer] = React.useState(
    () =>
      new QueriesObserver<TCombinedResult>(
        client,
        defaultedQueries,
        options as QueriesObserverOptions<TCombinedResult>,
      ),
  )

  // note: this must be called before useSyncExternalStore
  const [optimisticResult, getCombinedResult, trackResult] =
    observer.getOptimisticResult(
      defaultedQueries,
      (options as QueriesObserverOptions<TCombinedResult>).combine,
    )

  const shouldSubscribe = !isRestoring && options.subscribed !== false
  React.useSyncExternalStore(
    React.useCallback(
      (onStoreChange) =>
        shouldSubscribe
          ? observer.subscribe(notifyManager.batchCalls(onStoreChange))
          : noop,
      [observer, shouldSubscribe],
    ),
    () => observer.getCurrentResult(),
    () => observer.getCurrentResult(),
  )

  React.useEffect(() => {
    observer.setQueries(
      defaultedQueries,
      options as QueriesObserverOptions<TCombinedResult>,
    )
  }, [defaultedQueries, options, observer])

  const shouldAtLeastOneSuspend = optimisticResult.some((result, index) =>
    shouldSuspend(defaultedQueries[index], result),
  )

  const suspensePromises = shouldAtLeastOneSuspend
    ? optimisticResult.flatMap((result, index) => {
        const opts = defaultedQueries[index]

        if (opts) {
          const queryObserver = new QueryObserver(client, opts)
          if (shouldSuspend(opts, result)) {
            return fetchOptimistic(opts, queryObserver, errorResetBoundary)
          } else if (willFetch(result, isRestoring)) {
            void fetchOptimistic(opts, queryObserver, errorResetBoundary)
          }
        }
        return []
      })
    : []

  if (suspensePromises.length > 0) {
    throw Promise.all(suspensePromises)
  }
  const firstSingleResultWhichShouldThrow = optimisticResult.find(
    (result, index) => {
      const query = defaultedQueries[index]
      return (
        query &&
        getHasError({
          result,
          errorResetBoundary,
          throwOnError: query.throwOnError,
          query: client.getQueryCache().get(query.queryHash),
          suspense: query.suspense,
        })
      )
    },
  )

  if (firstSingleResultWhichShouldThrow?.error) {
    throw firstSingleResultWhichShouldThrow.error
  }

  return getCombinedResult(trackResult())
}
