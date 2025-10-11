/* istanbul ignore file */

import type { QueryClient } from './queryClient'
import type { DehydrateOptions, HydrateOptions } from './hydration'
import type { MutationState } from './mutation'
import type { FetchDirection, Query, QueryBehavior } from './query'
import type { RetryDelayValue, RetryValue } from './retryer'
import type { QueryFilters, QueryTypeFilter, SkipToken } from './utils'
import type { QueryCache } from './queryCache'
import type { MutationCache } from './mutationCache'

export type NonUndefinedGuard<T> = T extends undefined ? never : T

export type DistributiveOmit<
  TObject,
  TKey extends keyof TObject,
> = TObject extends any ? Omit<TObject, TKey> : never

export type OmitKeyof<
  TObject,
  TKey extends TStrictly extends 'safely'
    ?
        | keyof TObject
        | (string & Record<never, never>)
        | (number & Record<never, never>)
        | (symbol & Record<never, never>)
    : keyof TObject,
  TStrictly extends 'strictly' | 'safely' = 'strictly',
> = Omit<TObject, TKey>

export type Override<TTargetA, TTargetB> = {
  [AKey in keyof TTargetA]: AKey extends keyof TTargetB
    ? TTargetB[AKey]
    : TTargetA[AKey]
}

export type NoInfer<T> = [T][T extends any ? 0 : never]

export interface Register {
  // defaultError: Error
  // queryMeta: Record<string, unknown>
  // mutationMeta: Record<string, unknown>
  // queryKey: ReadonlyArray<unknown>
  // mutationKey: ReadonlyArray<unknown>
}

export type DefaultError = Register extends {
  defaultError: infer TError
}
  ? TError
  : Error

export type QueryKey = Register extends {
  queryKey: infer TQueryKey
}
  ? TQueryKey extends ReadonlyArray<unknown>
    ? TQueryKey
    : TQueryKey extends Array<unknown>
      ? TQueryKey
      : ReadonlyArray<unknown>
  : ReadonlyArray<unknown>

export const dataTagSymbol = Symbol('dataTagSymbol')
export type dataTagSymbol = typeof dataTagSymbol
export const dataTagErrorSymbol = Symbol('dataTagErrorSymbol')
export type dataTagErrorSymbol = typeof dataTagErrorSymbol
export const unsetMarker = Symbol('unsetMarker')
export type UnsetMarker = typeof unsetMarker
export type AnyDataTag = {
  [dataTagSymbol]: any
  [dataTagErrorSymbol]: any
}
export type DataTag<
  TType,
  TValue,
  TError = UnsetMarker,
> = TType extends AnyDataTag
  ? TType
  : TType & {
      [dataTagSymbol]: TValue
      [dataTagErrorSymbol]: TError
    }

export type InferDataFromTag<TQueryFnData, TTaggedQueryKey extends QueryKey> =
  TTaggedQueryKey extends DataTag<unknown, infer TaggedValue, unknown>
    ? TaggedValue
    : TQueryFnData

export type InferErrorFromTag<TError, TTaggedQueryKey extends QueryKey> =
  TTaggedQueryKey extends DataTag<unknown, unknown, infer TaggedError>
    ? TaggedError extends UnsetMarker
      ? TError
      : TaggedError
    : TError

export type QueryFunction<
  T = unknown,
  TQueryKey extends QueryKey = QueryKey,
  TPageParam = never,
> = (context: QueryFunctionContext<TQueryKey, TPageParam>) => T | Promise<T>

export type StaleTime = number | 'static'

export type StaleTimeFunction<
  TQueryFnData = unknown,
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
> =
  | StaleTime
  | ((query: Query<TQueryFnData, TError, TData, TQueryKey>) => StaleTime)

export type Enabled<
  TQueryFnData = unknown,
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
> =
  | boolean
  | ((query: Query<TQueryFnData, TError, TData, TQueryKey>) => boolean)

export type QueryPersister<
  T = unknown,
  TQueryKey extends QueryKey = QueryKey,
  TPageParam = never,
> = [TPageParam] extends [never]
  ? (
      queryFn: QueryFunction<T, TQueryKey, never>,
      context: QueryFunctionContext<TQueryKey>,
      query: Query,
    ) => T | Promise<T>
  : (
      queryFn: QueryFunction<T, TQueryKey, TPageParam>,
      context: QueryFunctionContext<TQueryKey>,
      query: Query,
    ) => T | Promise<T>

export type QueryFunctionContext<
  TQueryKey extends QueryKey = QueryKey,
  TPageParam = never,
> = [TPageParam] extends [never]
  ? {
      client: QueryClient
      queryKey: TQueryKey
      signal: AbortSignal
      meta: QueryMeta | undefined
      pageParam?: unknown
      /**
       * @deprecated
       * if you want access to the direction, you can add it to the pageParam
       */
      direction?: unknown
    }
  : {
      client: QueryClient
      queryKey: TQueryKey
      signal: AbortSignal
      pageParam: TPageParam
      /**
       * @deprecated
       * if you want access to the direction, you can add it to the pageParam
       */
      direction: FetchDirection
      meta: QueryMeta | undefined
    }

export type InitialDataFunction<T> = () => T | undefined

type NonFunctionGuard<T> = T extends Function ? never : T

export type PlaceholderDataFunction<
  TQueryFnData = unknown,
  TError = DefaultError,
  TQueryData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
> = (
  previousData: TQueryData | undefined,
  previousQuery: Query<TQueryFnData, TError, TQueryData, TQueryKey> | undefined,
) => TQueryData | undefined

export type QueriesPlaceholderDataFunction<TQueryData> = (
  previousData: undefined,
  previousQuery: undefined,
) => TQueryData | undefined

export type QueryKeyHashFunction<TQueryKey extends QueryKey> = (
  queryKey: TQueryKey,
) => string

export type GetPreviousPageParamFunction<TPageParam, TQueryFnData = unknown> = (
  firstPage: TQueryFnData,
  allPages: Array<TQueryFnData>,
  firstPageParam: TPageParam,
  allPageParams: Array<TPageParam>,
) => TPageParam | undefined | null

export type GetNextPageParamFunction<TPageParam, TQueryFnData = unknown> = (
  lastPage: TQueryFnData,
  allPages: Array<TQueryFnData>,
  lastPageParam: TPageParam,
  allPageParams: Array<TPageParam>,
) => TPageParam | undefined | null

export interface InfiniteData<TData, TPageParam = unknown> {
  pages: Array<TData>
  pageParams: Array<TPageParam>
}

export type QueryMeta = Register extends {
  queryMeta: infer TQueryMeta
}
  ? TQueryMeta extends Record<string, unknown>
    ? TQueryMeta
    : Record<string, unknown>
  : Record<string, unknown>

export type NetworkMode = 'online' | 'always' | 'offlineFirst'

export type NotifyOnChangeProps =
  | Array<keyof InfiniteQueryObserverResult>
  | 'all'
  | undefined
  | (() => Array<keyof InfiniteQueryObserverResult> | 'all' | undefined)

export interface QueryOptions<
  TQueryFnData = unknown,
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
  TPageParam = never,
> {
  /**
   * If `false`, failed queries will not retry by default.
   * If `true`, failed queries will retry infinitely., failureCount: num
   * If set to an integer number, e.g. 3, failed queries will retry until the failed query count meets that number.
   * If set to a function `(failureCount, error) => boolean` failed queries will retry until the function returns false.
   */
  retry?: RetryValue<TError>
  retryDelay?: RetryDelayValue<TError>
  networkMode?: NetworkMode
  /**
   * The time in milliseconds that unused/inactive cache data remains in memory.
   * When a query's cache becomes unused or inactive, that cache data will be garbage collected after this duration.
   * When different garbage collection times are specified, the longest one will be used.
   * Setting it to `Infinity` will disable garbage collection.
   */
  gcTime?: number
  queryFn?: QueryFunction<TQueryFnData, TQueryKey, TPageParam> | SkipToken
  persister?: QueryPersister<
    NoInfer<TQueryFnData>,
    NoInfer<TQueryKey>,
    NoInfer<TPageParam>
  >
  queryHash?: string
  queryKey?: TQueryKey
  queryKeyHashFn?: QueryKeyHashFunction<TQueryKey>
  initialData?: TData | InitialDataFunction<TData>
  initialDataUpdatedAt?: number | (() => number | undefined)
  behavior?: QueryBehavior<TQueryFnData, TError, TData, TQueryKey>
  /**
   * Set this to `false` to disable structural sharing between query results.
   * Set this to a function which accepts the old and new data and returns resolved data of the same type to implement custom structural sharing logic.
   * Defaults to `true`.
   */
  structuralSharing?:
    | boolean
    | ((oldData: unknown | undefined, newData: unknown) => unknown)
  _defaulted?: boolean
  /**
   * Additional payload to be stored on each query.
   * Use this property to pass information that can be used in other places.
   */
  meta?: QueryMeta
  /**
   * Maximum number of pages to store in the data of an infinite query.
   */
  maxPages?: number
}

export interface InitialPageParam<TPageParam = unknown> {
  initialPageParam: TPageParam
}

export interface InfiniteQueryPageParamsOptions<
  TQueryFnData = unknown,
  TPageParam = unknown,
> extends InitialPageParam<TPageParam> {
  /**
   * This function can be set to automatically get the previous cursor for infinite queries.
   * The result will also be used to determine the value of `hasPreviousPage`.
   */
  getPreviousPageParam?: GetPreviousPageParamFunction<TPageParam, TQueryFnData>
  /**
   * This function can be set to automatically get the next cursor for infinite queries.
   * The result will also be used to determine the value of `hasNextPage`.
   */
  getNextPageParam: GetNextPageParamFunction<TPageParam, TQueryFnData>
}

export type ThrowOnError<
  TQueryFnData,
  TError,
  TQueryData,
  TQueryKey extends QueryKey,
> =
  | boolean
  | ((
      error: TError,
      query: Query<TQueryFnData, TError, TQueryData, TQueryKey>,
    ) => boolean)

export interface QueryObserverOptions<
  TQueryFnData = unknown,
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
  TPageParam = never,
> extends WithRequired<
    QueryOptions<TQueryFnData, TError, TQueryData, TQueryKey, TPageParam>,
    'queryKey'
  > {
  /**
   * Set this to `false` or a function that returns `false` to disable automatic refetching when the query mounts or changes query keys.
   * To refetch the query, use the `refetch` method returned from the `useQuery` instance.
   * Accepts a boolean or function that returns a boolean.
   * Defaults to `true`.
   */
  enabled?: Enabled<TQueryFnData, TError, TQueryData, TQueryKey>
  /**
   * The time in milliseconds after data is considered stale.
   * If set to `Infinity`, the data will never be considered stale.
   * If set to a function, the function will be executed with the query to compute a `staleTime`.
   * Defaults to `0`.
   */
  staleTime?: StaleTimeFunction<TQueryFnData, TError, TQueryData, TQueryKey>
  /**
   * If set to a number, the query will continuously refetch at this frequency in milliseconds.
   * If set to a function, the function will be executed with the latest data and query to compute a frequency
   * Defaults to `false`.
   */
  refetchInterval?:
    | number
    | false
    | ((
        query: Query<TQueryFnData, TError, TQueryData, TQueryKey>,
      ) => number | false | undefined)
  /**
   * If set to `true`, the query will continue to refetch while their tab/window is in the background.
   * Defaults to `false`.
   */
  refetchIntervalInBackground?: boolean
  /**
   * If set to `true`, the query will refetch on window focus if the data is stale.
   * If set to `false`, the query will not refetch on window focus.
   * If set to `'always'`, the query will always refetch on window focus.
   * If set to a function, the function will be executed with the latest data and query to compute the value.
   * Defaults to `true`.
   */
  refetchOnWindowFocus?:
    | boolean
    | 'always'
    | ((
        query: Query<TQueryFnData, TError, TQueryData, TQueryKey>,
      ) => boolean | 'always')
  /**
   * If set to `true`, the query will refetch on reconnect if the data is stale.
   * If set to `false`, the query will not refetch on reconnect.
   * If set to `'always'`, the query will always refetch on reconnect.
   * If set to a function, the function will be executed with the latest data and query to compute the value.
   * Defaults to the value of `networkOnline` (`true`)
   */
  refetchOnReconnect?:
    | boolean
    | 'always'
    | ((
        query: Query<TQueryFnData, TError, TQueryData, TQueryKey>,
      ) => boolean | 'always')
  /**
   * If set to `true`, the query will refetch on mount if the data is stale.
   * If set to `false`, will disable additional instances of a query to trigger background refetch.
   * If set to `'always'`, the query will always refetch on mount.
   * If set to a function, the function will be executed with the latest data and query to compute the value
   * Defaults to `true`.
   */
  refetchOnMount?:
    | boolean
    | 'always'
    | ((
        query: Query<TQueryFnData, TError, TQueryData, TQueryKey>,
      ) => boolean | 'always')
  /**
   * If set to `false`, the query will not be retried on mount if it contains an error.
   * Defaults to `true`.
   */
  retryOnMount?: boolean
  /**
   * If set, the component will only re-render if any of the listed properties change.
   * When set to `['data', 'error']`, the component will only re-render when the `data` or `error` properties change.
   * When set to `'all'`, the component will re-render whenever a query is updated.
   * When set to a function, the function will be executed to compute the list of properties.
   * By default, access to properties will be tracked, and the component will only re-render when one of the tracked properties change.
   */
  notifyOnChangeProps?: NotifyOnChangeProps
  /**
   * Whether errors should be thrown instead of setting the `error` property.
   * If set to `true` or `suspense` is `true`, all errors will be thrown to the error boundary.
   * If set to `false` and `suspense` is `false`, errors are returned as state.
   * If set to a function, it will be passed the error and the query, and it should return a boolean indicating whether to show the error in an error boundary (`true`) or return the error as state (`false`).
   * Defaults to `false`.
   */
  throwOnError?: ThrowOnError<TQueryFnData, TError, TQueryData, TQueryKey>
  /**
   * This option can be used to transform or select a part of the data returned by the query function.
   */
  select?: (data: TQueryData) => TData
  /**
   * If set to `true`, the query will suspend when `status === 'pending'`
   * and throw errors when `status === 'error'`.
   * Defaults to `false`.
   */
  suspense?: boolean
  /**
   * If set, this value will be used as the placeholder data for this particular query observer while the query is still in the `loading` data and no initialData has been provided.
   */
  placeholderData?:
    | NonFunctionGuard<TQueryData>
    | PlaceholderDataFunction<
        NonFunctionGuard<TQueryData>,
        TError,
        NonFunctionGuard<TQueryData>,
        TQueryKey
      >

  _optimisticResults?: 'optimistic' | 'isRestoring'

  /**
   * Enable prefetching during rendering
   */
  experimental_prefetchInRender?: boolean
}

export type WithRequired<TTarget, TKey extends keyof TTarget> = TTarget & {
  [_ in TKey]: {}
}

export type DefaultedQueryObserverOptions<
  TQueryFnData = unknown,
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
> = WithRequired<
  QueryObserverOptions<TQueryFnData, TError, TData, TQueryData, TQueryKey>,
  'throwOnError' | 'refetchOnReconnect' | 'queryHash'
>

export interface InfiniteQueryObserverOptions<
  TQueryFnData = unknown,
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
  TPageParam = unknown,
> extends QueryObserverOptions<
      TQueryFnData,
      TError,
      TData,
      InfiniteData<TQueryFnData, TPageParam>,
      TQueryKey,
      TPageParam
    >,
    InfiniteQueryPageParamsOptions<TQueryFnData, TPageParam> {}

export type DefaultedInfiniteQueryObserverOptions<
  TQueryFnData = unknown,
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
  TPageParam = unknown,
> = WithRequired<
  InfiniteQueryObserverOptions<
    TQueryFnData,
    TError,
    TData,
    TQueryKey,
    TPageParam
  >,
  'throwOnError' | 'refetchOnReconnect' | 'queryHash'
>

export interface FetchQueryOptions<
  TQueryFnData = unknown,
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
  TPageParam = never,
> extends WithRequired<
    QueryOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam>,
    'queryKey'
  > {
  initialPageParam?: never
  /**
   * The time in milliseconds after data is considered stale.
   * If the data is fresh it will be returned from the cache.
   */
  staleTime?: StaleTimeFunction<TQueryFnData, TError, TData, TQueryKey>
}

export interface EnsureQueryDataOptions<
  TQueryFnData = unknown,
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
  TPageParam = never,
> extends FetchQueryOptions<
    TQueryFnData,
    TError,
    TData,
    TQueryKey,
    TPageParam
  > {
  revalidateIfStale?: boolean
}

export type EnsureInfiniteQueryDataOptions<
  TQueryFnData = unknown,
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
  TPageParam = unknown,
> = FetchInfiniteQueryOptions<
  TQueryFnData,
  TError,
  TData,
  TQueryKey,
  TPageParam
> & {
  revalidateIfStale?: boolean
}

type FetchInfiniteQueryPages<TQueryFnData = unknown, TPageParam = unknown> =
  | { pages?: never }
  | {
      pages: number
      getNextPageParam: GetNextPageParamFunction<TPageParam, TQueryFnData>
    }

export type FetchInfiniteQueryOptions<
  TQueryFnData = unknown,
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
  TPageParam = unknown,
> = Omit<
  FetchQueryOptions<
    TQueryFnData,
    TError,
    InfiniteData<TData, TPageParam>,
    TQueryKey,
    TPageParam
  >,
  'initialPageParam'
> &
  InitialPageParam<TPageParam> &
  FetchInfiniteQueryPages<TQueryFnData, TPageParam>

export interface ResultOptions {
  throwOnError?: boolean
}

export interface RefetchOptions extends ResultOptions {
  /**
   * If set to `true`, a currently running request will be cancelled before a new request is made
   *
   * If set to `false`, no refetch will be made if there is already a request running.
   *
   * Defaults to `true`.
   */
  cancelRefetch?: boolean
}

export interface InvalidateQueryFilters<TQueryKey extends QueryKey = QueryKey>
  extends QueryFilters<TQueryKey> {
  refetchType?: QueryTypeFilter | 'none'
}

export interface RefetchQueryFilters<TQueryKey extends QueryKey = QueryKey>
  extends QueryFilters<TQueryKey> {}

export interface InvalidateOptions extends RefetchOptions {}
export interface ResetOptions extends RefetchOptions {}

export interface FetchNextPageOptions extends ResultOptions {
  /**
   * If set to `true`, calling `fetchNextPage` repeatedly will invoke `queryFn` every time,
   * whether the previous invocation has resolved or not. Also, the result from previous invocations will be ignored.
   *
   * If set to `false`, calling `fetchNextPage` repeatedly won't have any effect until the first invocation has resolved.
   *
   * Defaults to `true`.
   */
  cancelRefetch?: boolean
}

export interface FetchPreviousPageOptions extends ResultOptions {
  /**
   * If set to `true`, calling `fetchPreviousPage` repeatedly will invoke `queryFn` every time,
   * whether the previous invocation has resolved or not. Also, the result from previous invocations will be ignored.
   *
   * If set to `false`, calling `fetchPreviousPage` repeatedly won't have any effect until the first invocation has resolved.
   *
   * Defaults to `true`.
   */
  cancelRefetch?: boolean
}

export type QueryStatus = 'pending' | 'error' | 'success'
export type FetchStatus = 'fetching' | 'paused' | 'idle'

export interface QueryObserverBaseResult<
  TData = unknown,
  TError = DefaultError,
> {
  /**
   * The last successfully resolved data for the query.
   */
  data: TData | undefined
  /**
   * The timestamp for when the query most recently returned the `status` as `"success"`.
   */
  dataUpdatedAt: number
  /**
   * The error object for the query, if an error was thrown.
   * - Defaults to `null`.
   */
  error: TError | null
  /**
   * The timestamp for when the query most recently returned the `status` as `"error"`.
   */
  errorUpdatedAt: number
  /**
   * The failure count for the query.
   * - Incremented every time the query fails.
   * - Reset to `0` when the query succeeds.
   */
  failureCount: number
  /**
   * The failure reason for the query retry.
   * - Reset to `null` when the query succeeds.
   */
  failureReason: TError | null
  /**
   * The sum of all errors.
   */
  errorUpdateCount: number
  /**
   * A derived boolean from the `status` variable, provided for convenience.
   * - `true` if the query attempt resulted in an error.
   */
  isError: boolean
  /**
   * Will be `true` if the query has been fetched.
   */
  isFetched: boolean
  /**
   * Will be `true` if the query has been fetched after the component mounted.
   * - This property can be used to not show any previously cached data.
   */
  isFetchedAfterMount: boolean
  /**
   * A derived boolean from the `fetchStatus` variable, provided for convenience.
   * - `true` whenever the `queryFn` is executing, which includes initial `pending` as well as background refetch.
   */
  isFetching: boolean
  /**
   * Is `true` whenever the first fetch for a query is in-flight.
   * - Is the same as `isFetching && isPending`.
   */
  isLoading: boolean
  /**
   * Will be `pending` if there's no cached data and no query attempt was finished yet.
   */
  isPending: boolean
  /**
   * Will be `true` if the query failed while fetching for the first time.
   */
  isLoadingError: boolean
  /**
   * @deprecated `isInitialLoading` is being deprecated in favor of `isLoading`
   * and will be removed in the next major version.
   */
  isInitialLoading: boolean
  /**
   * A derived boolean from the `fetchStatus` variable, provided for convenience.
   * - The query wanted to fetch, but has been `paused`.
   */
  isPaused: boolean
  /**
   * Will be `true` if the data shown is the placeholder data.
   */
  isPlaceholderData: boolean
  /**
   * Will be `true` if the query failed while refetching.
   */
  isRefetchError: boolean
  /**
   * Is `true` whenever a background refetch is in-flight, which _does not_ include initial `pending`.
   * - Is the same as `isFetching && !isPending`.
   */
  isRefetching: boolean
  /**
   * Will be `true` if the data in the cache is invalidated or if the data is older than the given `staleTime`.
   */
  isStale: boolean
  /**
   * A derived boolean from the `status` variable, provided for convenience.
   * - `true` if the query has received a response with no errors and is ready to display its data.
   */
  isSuccess: boolean
  /**
   * `true` if this observer is enabled, `false` otherwise.
   */
  isEnabled: boolean
  /**
   * A function to manually refetch the query.
   */
  refetch: (
    options?: RefetchOptions,
  ) => Promise<QueryObserverResult<TData, TError>>
  /**
   * The status of the query.
   * - Will be:
   *   - `pending` if there's no cached data and no query attempt was finished yet.
   *   - `error` if the query attempt resulted in an error.
   *   - `success` if the query has received a response with no errors and is ready to display its data.
   */
  status: QueryStatus
  /**
   * The fetch status of the query.
   * - `fetching`: Is `true` whenever the queryFn is executing, which includes initial `pending` as well as background refetch.
   * - `paused`: The query wanted to fetch, but has been `paused`.
   * - `idle`: The query is not fetching.
   * - See [Network Mode](https://tanstack.com/query/latest/docs/framework/react/guides/network-mode) for more information.
   */
  fetchStatus: FetchStatus
  /**
   * A stable promise that will be resolved with the data of the query.
   * Requires the `experimental_prefetchInRender` feature flag to be enabled.
   * @example
   *
   * ### Enabling the feature flag
   * ```ts
   * const client = new QueryClient({
   *   defaultOptions: {
   *     queries: {
   *       experimental_prefetchInRender: true,
   *     },
   *   },
   * })
   * ```
   *
   * ### Usage
   * ```tsx
   * import { useQuery } from '@tanstack/react-query'
   * import React from 'react'
   * import { fetchTodos, type Todo } from './api'
   *
   * function TodoList({ query }: { query: UseQueryResult<Todo[], Error> }) {
   *   const data = React.use(query.promise)
   *
   *   return (
   *     <ul>
   *       {data.map(todo => (
   *         <li key={todo.id}>{todo.title}</li>
   *       ))}
   *     </ul>
   *   )
   * }
   *
   * export function App() {
   *   const query = useQuery({ queryKey: ['todos'], queryFn: fetchTodos })
   *
   *   return (
   *     <>
   *       <h1>Todos</h1>
   *       <React.Suspense fallback={<div>Loading...</div>}>
   *         <TodoList query={query} />
   *       </React.Suspense>
   *     </>
   *   )
   * }
   * ```
   */
  promise: Promise<TData>
}

export interface QueryObserverPendingResult<
  TData = unknown,
  TError = DefaultError,
> extends QueryObserverBaseResult<TData, TError> {
  data: undefined
  error: null
  isError: false
  isPending: true
  isLoadingError: false
  isRefetchError: false
  isSuccess: false
  isPlaceholderData: false
  status: 'pending'
}

export interface QueryObserverLoadingResult<
  TData = unknown,
  TError = DefaultError,
> extends QueryObserverBaseResult<TData, TError> {
  data: undefined
  error: null
  isError: false
  isPending: true
  isLoading: true
  isLoadingError: false
  isRefetchError: false
  isSuccess: false
  isPlaceholderData: false
  status: 'pending'
}

export interface QueryObserverLoadingErrorResult<
  TData = unknown,
  TError = DefaultError,
> extends QueryObserverBaseResult<TData, TError> {
  data: undefined
  error: TError
  isError: true
  isPending: false
  isLoading: false
  isLoadingError: true
  isRefetchError: false
  isSuccess: false
  isPlaceholderData: false
  status: 'error'
}

export interface QueryObserverRefetchErrorResult<
  TData = unknown,
  TError = DefaultError,
> extends QueryObserverBaseResult<TData, TError> {
  data: TData
  error: TError
  isError: true
  isPending: false
  isLoading: false
  isLoadingError: false
  isRefetchError: true
  isSuccess: false
  isPlaceholderData: false
  status: 'error'
}

export interface QueryObserverSuccessResult<
  TData = unknown,
  TError = DefaultError,
> extends QueryObserverBaseResult<TData, TError> {
  data: TData
  error: null
  isError: false
  isPending: false
  isLoading: false
  isLoadingError: false
  isRefetchError: false
  isSuccess: true
  isPlaceholderData: false
  status: 'success'
}

export interface QueryObserverPlaceholderResult<
  TData = unknown,
  TError = DefaultError,
> extends QueryObserverBaseResult<TData, TError> {
  data: TData
  isError: false
  error: null
  isPending: false
  isLoading: false
  isLoadingError: false
  isRefetchError: false
  isSuccess: true
  isPlaceholderData: true
  status: 'success'
}

export type DefinedQueryObserverResult<
  TData = unknown,
  TError = DefaultError,
> =
  | QueryObserverRefetchErrorResult<TData, TError>
  | QueryObserverSuccessResult<TData, TError>

export type QueryObserverResult<TData = unknown, TError = DefaultError> =
  | DefinedQueryObserverResult<TData, TError>
  | QueryObserverLoadingErrorResult<TData, TError>
  | QueryObserverLoadingResult<TData, TError>
  | QueryObserverPendingResult<TData, TError>
  | QueryObserverPlaceholderResult<TData, TError>

export interface InfiniteQueryObserverBaseResult<
  TData = unknown,
  TError = DefaultError,
> extends QueryObserverBaseResult<TData, TError> {
  /**
   * This function allows you to fetch the next "page" of results.
   */
  fetchNextPage: (
    options?: FetchNextPageOptions,
  ) => Promise<InfiniteQueryObserverResult<TData, TError>>
  /**
   * This function allows you to fetch the previous "page" of results.
   */
  fetchPreviousPage: (
    options?: FetchPreviousPageOptions,
  ) => Promise<InfiniteQueryObserverResult<TData, TError>>
  /**
   * Will be `true` if there is a next page to be fetched (known via the `getNextPageParam` option).
   */
  hasNextPage: boolean
  /**
   * Will be `true` if there is a previous page to be fetched (known via the `getPreviousPageParam` option).
   */
  hasPreviousPage: boolean
  /**
   * Will be `true` if the query failed while fetching the next page.
   */
  isFetchNextPageError: boolean
  /**
   * Will be `true` while fetching the next page with `fetchNextPage`.
   */
  isFetchingNextPage: boolean
  /**
   * Will be `true` if the query failed while fetching the previous page.
   */
  isFetchPreviousPageError: boolean
  /**
   * Will be `true` while fetching the previous page with `fetchPreviousPage`.
   */
  isFetchingPreviousPage: boolean
}

export interface InfiniteQueryObserverPendingResult<
  TData = unknown,
  TError = DefaultError,
> extends InfiniteQueryObserverBaseResult<TData, TError> {
  data: undefined
  error: null
  isError: false
  isPending: true
  isLoadingError: false
  isRefetchError: false
  isFetchNextPageError: false
  isFetchPreviousPageError: false
  isSuccess: false
  isPlaceholderData: false
  status: 'pending'
}

export interface InfiniteQueryObserverLoadingResult<
  TData = unknown,
  TError = DefaultError,
> extends InfiniteQueryObserverBaseResult<TData, TError> {
  data: undefined
  error: null
  isError: false
  isPending: true
  isLoading: true
  isLoadingError: false
  isRefetchError: false
  isFetchNextPageError: false
  isFetchPreviousPageError: false
  isSuccess: false
  isPlaceholderData: false
  status: 'pending'
}

export interface InfiniteQueryObserverLoadingErrorResult<
  TData = unknown,
  TError = DefaultError,
> extends InfiniteQueryObserverBaseResult<TData, TError> {
  data: undefined
  error: TError
  isError: true
  isPending: false
  isLoading: false
  isLoadingError: true
  isRefetchError: false
  isFetchNextPageError: false
  isFetchPreviousPageError: false
  isSuccess: false
  isPlaceholderData: false
  status: 'error'
}

export interface InfiniteQueryObserverRefetchErrorResult<
  TData = unknown,
  TError = DefaultError,
> extends InfiniteQueryObserverBaseResult<TData, TError> {
  data: TData
  error: TError
  isError: true
  isPending: false
  isLoading: false
  isLoadingError: false
  isRefetchError: true
  isSuccess: false
  isPlaceholderData: false
  status: 'error'
}

export interface InfiniteQueryObserverSuccessResult<
  TData = unknown,
  TError = DefaultError,
> extends InfiniteQueryObserverBaseResult<TData, TError> {
  data: TData
  error: null
  isError: false
  isPending: false
  isLoading: false
  isLoadingError: false
  isRefetchError: false
  isFetchNextPageError: false
  isFetchPreviousPageError: false
  isSuccess: true
  isPlaceholderData: false
  status: 'success'
}

export interface InfiniteQueryObserverPlaceholderResult<
  TData = unknown,
  TError = DefaultError,
> extends InfiniteQueryObserverBaseResult<TData, TError> {
  data: TData
  isError: false
  error: null
  isPending: false
  isLoading: false
  isLoadingError: false
  isRefetchError: false
  isSuccess: true
  isPlaceholderData: true
  isFetchNextPageError: false
  isFetchPreviousPageError: false
  status: 'success'
}

export type DefinedInfiniteQueryObserverResult<
  TData = unknown,
  TError = DefaultError,
> =
  | InfiniteQueryObserverRefetchErrorResult<TData, TError>
  | InfiniteQueryObserverSuccessResult<TData, TError>

export type InfiniteQueryObserverResult<
  TData = unknown,
  TError = DefaultError,
> =
  | DefinedInfiniteQueryObserverResult<TData, TError>
  | InfiniteQueryObserverLoadingErrorResult<TData, TError>
  | InfiniteQueryObserverLoadingResult<TData, TError>
  | InfiniteQueryObserverPendingResult<TData, TError>
  | InfiniteQueryObserverPlaceholderResult<TData, TError>

export type MutationKey = Register extends {
  mutationKey: infer TMutationKey
}
  ? TMutationKey extends Array<unknown>
    ? TMutationKey
    : TMutationKey extends Array<unknown>
      ? TMutationKey
      : ReadonlyArray<unknown>
  : ReadonlyArray<unknown>

export type MutationStatus = 'idle' | 'pending' | 'success' | 'error'

export type MutationScope = {
  id: string
}

export type MutationMeta = Register extends {
  mutationMeta: infer TMutationMeta
}
  ? TMutationMeta extends Record<string, unknown>
    ? TMutationMeta
    : Record<string, unknown>
  : Record<string, unknown>

export type MutationFunctionContext = {
  client: QueryClient
  meta: MutationMeta | undefined
  mutationKey?: MutationKey
}

export type MutationFunction<TData = unknown, TVariables = unknown> = (
  variables: TVariables,
  context: MutationFunctionContext,
) => Promise<TData>

export interface MutationOptions<
  TData = unknown,
  TError = DefaultError,
  TVariables = void,
  TOnMutateResult = unknown,
> {
  mutationFn?: MutationFunction<TData, TVariables>
  mutationKey?: MutationKey
  onMutate?: (
    variables: TVariables,
    context: MutationFunctionContext,
  ) => Promise<TOnMutateResult> | TOnMutateResult
  onSuccess?: (
    data: TData,
    variables: TVariables,
    onMutateResult: TOnMutateResult,
    context: MutationFunctionContext,
  ) => Promise<unknown> | unknown
  onError?: (
    error: TError,
    variables: TVariables,
    onMutateResult: TOnMutateResult | undefined,
    context: MutationFunctionContext,
  ) => Promise<unknown> | unknown
  onSettled?: (
    data: TData | undefined,
    error: TError | null,
    variables: TVariables,
    onMutateResult: TOnMutateResult | undefined,
    context: MutationFunctionContext,
  ) => Promise<unknown> | unknown
  retry?: RetryValue<TError>
  retryDelay?: RetryDelayValue<TError>
  networkMode?: NetworkMode
  gcTime?: number
  _defaulted?: boolean
  meta?: MutationMeta
  scope?: MutationScope
}

export interface MutationObserverOptions<
  TData = unknown,
  TError = DefaultError,
  TVariables = void,
  TOnMutateResult = unknown,
> extends MutationOptions<TData, TError, TVariables, TOnMutateResult> {
  throwOnError?: boolean | ((error: TError) => boolean)
}

export interface MutateOptions<
  TData = unknown,
  TError = DefaultError,
  TVariables = void,
  TOnMutateResult = unknown,
> {
  onSuccess?: (
    data: TData,
    variables: TVariables,
    onMutateResult: TOnMutateResult | undefined,
    context: MutationFunctionContext,
  ) => void
  onError?: (
    error: TError,
    variables: TVariables,
    onMutateResult: TOnMutateResult | undefined,
    context: MutationFunctionContext,
  ) => void
  onSettled?: (
    data: TData | undefined,
    error: TError | null,
    variables: TVariables,
    onMutateResult: TOnMutateResult | undefined,
    context: MutationFunctionContext,
  ) => void
}

export type MutateFunction<
  TData = unknown,
  TError = DefaultError,
  TVariables = void,
  TOnMutateResult = unknown,
> = (
  variables: TVariables,
  options?: MutateOptions<TData, TError, TVariables, TOnMutateResult>,
) => Promise<TData>

export interface MutationObserverBaseResult<
  TData = unknown,
  TError = DefaultError,
  TVariables = void,
  TOnMutateResult = unknown,
> extends MutationState<TData, TError, TVariables, TOnMutateResult> {
  /**
   * The last successfully resolved data for the mutation.
   */
  data: TData | undefined
  /**
   * The variables object passed to the `mutationFn`.
   */
  variables: TVariables | undefined
  /**
   * The error object for the mutation, if an error was encountered.
   * - Defaults to `null`.
   */
  error: TError | null
  /**
   * A boolean variable derived from `status`.
   * - `true` if the last mutation attempt resulted in an error.
   */
  isError: boolean
  /**
   * A boolean variable derived from `status`.
   * - `true` if the mutation is in its initial state prior to executing.
   */
  isIdle: boolean
  /**
   * A boolean variable derived from `status`.
   * - `true` if the mutation is currently executing.
   */
  isPending: boolean
  /**
   * A boolean variable derived from `status`.
   * - `true` if the last mutation attempt was successful.
   */
  isSuccess: boolean
  /**
   * The status of the mutation.
   * - Will be:
   *   - `idle` initial status prior to the mutation function executing.
   *   - `pending` if the mutation is currently executing.
   *   - `error` if the last mutation attempt resulted in an error.
   *   - `success` if the last mutation attempt was successful.
   */
  status: MutationStatus
  /**
   * The mutation function you can call with variables to trigger the mutation and optionally hooks on additional callback options.
   * @param variables - The variables object to pass to the `mutationFn`.
   * @param options.onSuccess - This function will fire when the mutation is successful and will be passed the mutation's result.
   * @param options.onError - This function will fire if the mutation encounters an error and will be passed the error.
   * @param options.onSettled - This function will fire when the mutation is either successfully fetched or encounters an error and be passed either the data or error.
   * @remarks
   * - If you make multiple requests, `onSuccess` will fire only after the latest call you've made.
   * - All the callback functions (`onSuccess`, `onError`, `onSettled`) are void functions, and the returned value will be ignored.
   */
  mutate: MutateFunction<TData, TError, TVariables, TOnMutateResult>
  /**
   * A function to clean the mutation internal state (i.e., it resets the mutation to its initial state).
   */
  reset: () => void
}

export interface MutationObserverIdleResult<
  TData = unknown,
  TError = DefaultError,
  TVariables = void,
  TOnMutateResult = unknown,
> extends MutationObserverBaseResult<
    TData,
    TError,
    TVariables,
    TOnMutateResult
  > {
  data: undefined
  variables: undefined
  error: null
  isError: false
  isIdle: true
  isPending: false
  isSuccess: false
  status: 'idle'
}

export interface MutationObserverLoadingResult<
  TData = unknown,
  TError = DefaultError,
  TVariables = void,
  TOnMutateResult = unknown,
> extends MutationObserverBaseResult<
    TData,
    TError,
    TVariables,
    TOnMutateResult
  > {
  data: undefined
  variables: TVariables
  error: null
  isError: false
  isIdle: false
  isPending: true
  isSuccess: false
  status: 'pending'
}

export interface MutationObserverErrorResult<
  TData = unknown,
  TError = DefaultError,
  TVariables = void,
  TOnMutateResult = unknown,
> extends MutationObserverBaseResult<
    TData,
    TError,
    TVariables,
    TOnMutateResult
  > {
  data: undefined
  error: TError
  variables: TVariables
  isError: true
  isIdle: false
  isPending: false
  isSuccess: false
  status: 'error'
}

export interface MutationObserverSuccessResult<
  TData = unknown,
  TError = DefaultError,
  TVariables = void,
  TOnMutateResult = unknown,
> extends MutationObserverBaseResult<
    TData,
    TError,
    TVariables,
    TOnMutateResult
  > {
  data: TData
  error: null
  variables: TVariables
  isError: false
  isIdle: false
  isPending: false
  isSuccess: true
  status: 'success'
}

export type MutationObserverResult<
  TData = unknown,
  TError = DefaultError,
  TVariables = void,
  TOnMutateResult = unknown,
> =
  | MutationObserverIdleResult<TData, TError, TVariables, TOnMutateResult>
  | MutationObserverLoadingResult<TData, TError, TVariables, TOnMutateResult>
  | MutationObserverErrorResult<TData, TError, TVariables, TOnMutateResult>
  | MutationObserverSuccessResult<TData, TError, TVariables, TOnMutateResult>

export interface QueryClientConfig {
  queryCache?: QueryCache
  mutationCache?: MutationCache
  defaultOptions?: DefaultOptions
}

export interface DefaultOptions<TError = DefaultError> {
  queries?: OmitKeyof<
    QueryObserverOptions<unknown, TError>,
    'suspense' | 'queryKey'
  >
  mutations?: MutationObserverOptions<unknown, TError, unknown, unknown>
  hydrate?: HydrateOptions['defaultOptions']
  dehydrate?: DehydrateOptions
}

export interface CancelOptions {
  revert?: boolean
  silent?: boolean
}

export interface SetDataOptions {
  updatedAt?: number
}

export type NotifyEventType =
  | 'added'
  | 'removed'
  | 'updated'
  | 'observerAdded'
  | 'observerRemoved'
  | 'observerResultsUpdated'
  | 'observerOptionsUpdated'

export interface NotifyEvent {
  type: NotifyEventType
}
