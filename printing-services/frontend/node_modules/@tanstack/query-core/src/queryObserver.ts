import { focusManager } from './focusManager'
import { notifyManager } from './notifyManager'
import { fetchState } from './query'
import { Subscribable } from './subscribable'
import { pendingThenable } from './thenable'
import {
  isServer,
  isValidTimeout,
  noop,
  replaceData,
  resolveEnabled,
  resolveStaleTime,
  shallowEqualObjects,
  timeUntilStale,
} from './utils'
import { timeoutManager } from './timeoutManager'
import type { ManagedTimerId } from './timeoutManager'
import type { FetchOptions, Query, QueryState } from './query'
import type { QueryClient } from './queryClient'
import type { PendingThenable, Thenable } from './thenable'
import type {
  DefaultError,
  DefaultedQueryObserverOptions,
  PlaceholderDataFunction,
  QueryKey,
  QueryObserverBaseResult,
  QueryObserverOptions,
  QueryObserverResult,
  QueryOptions,
  RefetchOptions,
} from './types'

type QueryObserverListener<TData, TError> = (
  result: QueryObserverResult<TData, TError>,
) => void

interface ObserverFetchOptions extends FetchOptions {
  throwOnError?: boolean
}

export class QueryObserver<
  TQueryFnData = unknown,
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
> extends Subscribable<QueryObserverListener<TData, TError>> {
  #client: QueryClient
  #currentQuery: Query<TQueryFnData, TError, TQueryData, TQueryKey> = undefined!
  #currentQueryInitialState: QueryState<TQueryData, TError> = undefined!
  #currentResult: QueryObserverResult<TData, TError> = undefined!
  #currentResultState?: QueryState<TQueryData, TError>
  #currentResultOptions?: QueryObserverOptions<
    TQueryFnData,
    TError,
    TData,
    TQueryData,
    TQueryKey
  >
  #currentThenable: Thenable<TData>
  #selectError: TError | null
  #selectFn?: (data: TQueryData) => TData
  #selectResult?: TData
  // This property keeps track of the last query with defined data.
  // It will be used to pass the previous data and query to the placeholder function between renders.
  #lastQueryWithDefinedData?: Query<TQueryFnData, TError, TQueryData, TQueryKey>
  #staleTimeoutId?: ManagedTimerId
  #refetchIntervalId?: ManagedTimerId
  #currentRefetchInterval?: number | false
  #trackedProps = new Set<keyof QueryObserverResult>()

  constructor(
    client: QueryClient,
    public options: QueryObserverOptions<
      TQueryFnData,
      TError,
      TData,
      TQueryData,
      TQueryKey
    >,
  ) {
    super()

    this.#client = client
    this.#selectError = null
    this.#currentThenable = pendingThenable()

    this.bindMethods()
    this.setOptions(options)
  }

  protected bindMethods(): void {
    this.refetch = this.refetch.bind(this)
  }

  protected onSubscribe(): void {
    if (this.listeners.size === 1) {
      this.#currentQuery.addObserver(this)

      if (shouldFetchOnMount(this.#currentQuery, this.options)) {
        this.#executeFetch()
      } else {
        this.updateResult()
      }

      this.#updateTimers()
    }
  }

  protected onUnsubscribe(): void {
    if (!this.hasListeners()) {
      this.destroy()
    }
  }

  shouldFetchOnReconnect(): boolean {
    return shouldFetchOn(
      this.#currentQuery,
      this.options,
      this.options.refetchOnReconnect,
    )
  }

  shouldFetchOnWindowFocus(): boolean {
    return shouldFetchOn(
      this.#currentQuery,
      this.options,
      this.options.refetchOnWindowFocus,
    )
  }

  destroy(): void {
    this.listeners = new Set()
    this.#clearStaleTimeout()
    this.#clearRefetchInterval()
    this.#currentQuery.removeObserver(this)
  }

  setOptions(
    options: QueryObserverOptions<
      TQueryFnData,
      TError,
      TData,
      TQueryData,
      TQueryKey
    >,
  ): void {
    const prevOptions = this.options
    const prevQuery = this.#currentQuery

    this.options = this.#client.defaultQueryOptions(options)

    if (
      this.options.enabled !== undefined &&
      typeof this.options.enabled !== 'boolean' &&
      typeof this.options.enabled !== 'function' &&
      typeof resolveEnabled(this.options.enabled, this.#currentQuery) !==
        'boolean'
    ) {
      throw new Error(
        'Expected enabled to be a boolean or a callback that returns a boolean',
      )
    }

    this.#updateQuery()
    this.#currentQuery.setOptions(this.options)

    if (
      prevOptions._defaulted &&
      !shallowEqualObjects(this.options, prevOptions)
    ) {
      this.#client.getQueryCache().notify({
        type: 'observerOptionsUpdated',
        query: this.#currentQuery,
        observer: this,
      })
    }

    const mounted = this.hasListeners()

    // Fetch if there are subscribers
    if (
      mounted &&
      shouldFetchOptionally(
        this.#currentQuery,
        prevQuery,
        this.options,
        prevOptions,
      )
    ) {
      this.#executeFetch()
    }

    // Update result
    this.updateResult()

    // Update stale interval if needed
    if (
      mounted &&
      (this.#currentQuery !== prevQuery ||
        resolveEnabled(this.options.enabled, this.#currentQuery) !==
          resolveEnabled(prevOptions.enabled, this.#currentQuery) ||
        resolveStaleTime(this.options.staleTime, this.#currentQuery) !==
          resolveStaleTime(prevOptions.staleTime, this.#currentQuery))
    ) {
      this.#updateStaleTimeout()
    }

    const nextRefetchInterval = this.#computeRefetchInterval()

    // Update refetch interval if needed
    if (
      mounted &&
      (this.#currentQuery !== prevQuery ||
        resolveEnabled(this.options.enabled, this.#currentQuery) !==
          resolveEnabled(prevOptions.enabled, this.#currentQuery) ||
        nextRefetchInterval !== this.#currentRefetchInterval)
    ) {
      this.#updateRefetchInterval(nextRefetchInterval)
    }
  }

  getOptimisticResult(
    options: DefaultedQueryObserverOptions<
      TQueryFnData,
      TError,
      TData,
      TQueryData,
      TQueryKey
    >,
  ): QueryObserverResult<TData, TError> {
    const query = this.#client.getQueryCache().build(this.#client, options)

    const result = this.createResult(query, options)

    if (shouldAssignObserverCurrentProperties(this, result)) {
      // this assigns the optimistic result to the current Observer
      // because if the query function changes, useQuery will be performing
      // an effect where it would fetch again.
      // When the fetch finishes, we perform a deep data cloning in order
      // to reuse objects references. This deep data clone is performed against
      // the `observer.currentResult.data` property
      // When QueryKey changes, we refresh the query and get new `optimistic`
      // result, while we leave the `observer.currentResult`, so when new data
      // arrives, it finds the old `observer.currentResult` which is related
      // to the old QueryKey. Which means that currentResult and selectData are
      // out of sync already.
      // To solve this, we move the cursor of the currentResult every time
      // an observer reads an optimistic value.

      // When keeping the previous data, the result doesn't change until new
      // data arrives.
      this.#currentResult = result
      this.#currentResultOptions = this.options
      this.#currentResultState = this.#currentQuery.state
    }
    return result
  }

  getCurrentResult(): QueryObserverResult<TData, TError> {
    return this.#currentResult
  }

  trackResult(
    result: QueryObserverResult<TData, TError>,
    onPropTracked?: (key: keyof QueryObserverResult) => void,
  ): QueryObserverResult<TData, TError> {
    return new Proxy(result, {
      get: (target, key) => {
        this.trackProp(key as keyof QueryObserverResult)
        onPropTracked?.(key as keyof QueryObserverResult)
        if (
          key === 'promise' &&
          !this.options.experimental_prefetchInRender &&
          this.#currentThenable.status === 'pending'
        ) {
          this.#currentThenable.reject(
            new Error(
              'experimental_prefetchInRender feature flag is not enabled',
            ),
          )
        }
        return Reflect.get(target, key)
      },
    })
  }

  trackProp(key: keyof QueryObserverResult) {
    this.#trackedProps.add(key)
  }

  getCurrentQuery(): Query<TQueryFnData, TError, TQueryData, TQueryKey> {
    return this.#currentQuery
  }

  refetch({ ...options }: RefetchOptions = {}): Promise<
    QueryObserverResult<TData, TError>
  > {
    return this.fetch({
      ...options,
    })
  }

  fetchOptimistic(
    options: QueryObserverOptions<
      TQueryFnData,
      TError,
      TData,
      TQueryData,
      TQueryKey
    >,
  ): Promise<QueryObserverResult<TData, TError>> {
    const defaultedOptions = this.#client.defaultQueryOptions(options)

    const query = this.#client
      .getQueryCache()
      .build(this.#client, defaultedOptions)

    return query.fetch().then(() => this.createResult(query, defaultedOptions))
  }

  protected fetch(
    fetchOptions: ObserverFetchOptions,
  ): Promise<QueryObserverResult<TData, TError>> {
    return this.#executeFetch({
      ...fetchOptions,
      cancelRefetch: fetchOptions.cancelRefetch ?? true,
    }).then(() => {
      this.updateResult()
      return this.#currentResult
    })
  }

  #executeFetch(
    fetchOptions?: Omit<ObserverFetchOptions, 'initialPromise'>,
  ): Promise<TQueryData | undefined> {
    // Make sure we reference the latest query as the current one might have been removed
    this.#updateQuery()

    // Fetch
    let promise: Promise<TQueryData | undefined> = this.#currentQuery.fetch(
      this.options as QueryOptions<TQueryFnData, TError, TQueryData, TQueryKey>,
      fetchOptions,
    )

    if (!fetchOptions?.throwOnError) {
      promise = promise.catch(noop)
    }

    return promise
  }

  #updateStaleTimeout(): void {
    this.#clearStaleTimeout()
    const staleTime = resolveStaleTime(
      this.options.staleTime,
      this.#currentQuery,
    )

    if (isServer || this.#currentResult.isStale || !isValidTimeout(staleTime)) {
      return
    }

    const time = timeUntilStale(this.#currentResult.dataUpdatedAt, staleTime)

    // The timeout is sometimes triggered 1 ms before the stale time expiration.
    // To mitigate this issue we always add 1 ms to the timeout.
    const timeout = time + 1

    this.#staleTimeoutId = timeoutManager.setTimeout(() => {
      if (!this.#currentResult.isStale) {
        this.updateResult()
      }
    }, timeout)
  }

  #computeRefetchInterval() {
    return (
      (typeof this.options.refetchInterval === 'function'
        ? this.options.refetchInterval(this.#currentQuery)
        : this.options.refetchInterval) ?? false
    )
  }

  #updateRefetchInterval(nextInterval: number | false): void {
    this.#clearRefetchInterval()

    this.#currentRefetchInterval = nextInterval

    if (
      isServer ||
      resolveEnabled(this.options.enabled, this.#currentQuery) === false ||
      !isValidTimeout(this.#currentRefetchInterval) ||
      this.#currentRefetchInterval === 0
    ) {
      return
    }

    this.#refetchIntervalId = timeoutManager.setInterval(() => {
      if (
        this.options.refetchIntervalInBackground ||
        focusManager.isFocused()
      ) {
        this.#executeFetch()
      }
    }, this.#currentRefetchInterval)
  }

  #updateTimers(): void {
    this.#updateStaleTimeout()
    this.#updateRefetchInterval(this.#computeRefetchInterval())
  }

  #clearStaleTimeout(): void {
    if (this.#staleTimeoutId) {
      timeoutManager.clearTimeout(this.#staleTimeoutId)
      this.#staleTimeoutId = undefined
    }
  }

  #clearRefetchInterval(): void {
    if (this.#refetchIntervalId) {
      timeoutManager.clearInterval(this.#refetchIntervalId)
      this.#refetchIntervalId = undefined
    }
  }

  protected createResult(
    query: Query<TQueryFnData, TError, TQueryData, TQueryKey>,
    options: QueryObserverOptions<
      TQueryFnData,
      TError,
      TData,
      TQueryData,
      TQueryKey
    >,
  ): QueryObserverResult<TData, TError> {
    const prevQuery = this.#currentQuery
    const prevOptions = this.options
    const prevResult = this.#currentResult as
      | QueryObserverResult<TData, TError>
      | undefined
    const prevResultState = this.#currentResultState
    const prevResultOptions = this.#currentResultOptions
    const queryChange = query !== prevQuery
    const queryInitialState = queryChange
      ? query.state
      : this.#currentQueryInitialState

    const { state } = query
    let newState = { ...state }
    let isPlaceholderData = false
    let data: TData | undefined

    // Optimistically set result in fetching state if needed
    if (options._optimisticResults) {
      const mounted = this.hasListeners()

      const fetchOnMount = !mounted && shouldFetchOnMount(query, options)

      const fetchOptionally =
        mounted && shouldFetchOptionally(query, prevQuery, options, prevOptions)

      if (fetchOnMount || fetchOptionally) {
        newState = {
          ...newState,
          ...fetchState(state.data, query.options),
        }
      }
      if (options._optimisticResults === 'isRestoring') {
        newState.fetchStatus = 'idle'
      }
    }

    let { error, errorUpdatedAt, status } = newState

    // Per default, use query data
    data = newState.data as unknown as TData
    let skipSelect = false

    // use placeholderData if needed
    if (
      options.placeholderData !== undefined &&
      data === undefined &&
      status === 'pending'
    ) {
      let placeholderData

      // Memoize placeholder data
      if (
        prevResult?.isPlaceholderData &&
        options.placeholderData === prevResultOptions?.placeholderData
      ) {
        placeholderData = prevResult.data
        // we have to skip select when reading this memoization
        // because prevResult.data is already "selected"
        skipSelect = true
      } else {
        // compute placeholderData
        placeholderData =
          typeof options.placeholderData === 'function'
            ? (
                options.placeholderData as unknown as PlaceholderDataFunction<TQueryData>
              )(
                this.#lastQueryWithDefinedData?.state.data,
                this.#lastQueryWithDefinedData as any,
              )
            : options.placeholderData
      }

      if (placeholderData !== undefined) {
        status = 'success'
        data = replaceData(
          prevResult?.data,
          placeholderData as unknown,
          options,
        ) as TData
        isPlaceholderData = true
      }
    }

    // Select data if needed
    // this also runs placeholderData through the select function
    if (options.select && data !== undefined && !skipSelect) {
      // Memoize select result
      if (
        prevResult &&
        data === prevResultState?.data &&
        options.select === this.#selectFn
      ) {
        data = this.#selectResult
      } else {
        try {
          this.#selectFn = options.select
          data = options.select(data as any)
          data = replaceData(prevResult?.data, data, options)
          this.#selectResult = data
          this.#selectError = null
        } catch (selectError) {
          this.#selectError = selectError as TError
        }
      }
    }

    if (this.#selectError) {
      error = this.#selectError as any
      data = this.#selectResult
      errorUpdatedAt = Date.now()
      status = 'error'
    }

    const isFetching = newState.fetchStatus === 'fetching'
    const isPending = status === 'pending'
    const isError = status === 'error'

    const isLoading = isPending && isFetching
    const hasData = data !== undefined

    const result: QueryObserverBaseResult<TData, TError> = {
      status,
      fetchStatus: newState.fetchStatus,
      isPending,
      isSuccess: status === 'success',
      isError,
      isInitialLoading: isLoading,
      isLoading,
      data,
      dataUpdatedAt: newState.dataUpdatedAt,
      error,
      errorUpdatedAt,
      failureCount: newState.fetchFailureCount,
      failureReason: newState.fetchFailureReason,
      errorUpdateCount: newState.errorUpdateCount,
      isFetched: newState.dataUpdateCount > 0 || newState.errorUpdateCount > 0,
      isFetchedAfterMount:
        newState.dataUpdateCount > queryInitialState.dataUpdateCount ||
        newState.errorUpdateCount > queryInitialState.errorUpdateCount,
      isFetching,
      isRefetching: isFetching && !isPending,
      isLoadingError: isError && !hasData,
      isPaused: newState.fetchStatus === 'paused',
      isPlaceholderData,
      isRefetchError: isError && hasData,
      isStale: isStale(query, options),
      refetch: this.refetch,
      promise: this.#currentThenable,
      isEnabled: resolveEnabled(options.enabled, query) !== false,
    }

    const nextResult = result as QueryObserverResult<TData, TError>

    if (this.options.experimental_prefetchInRender) {
      const finalizeThenableIfPossible = (thenable: PendingThenable<TData>) => {
        if (nextResult.status === 'error') {
          thenable.reject(nextResult.error)
        } else if (nextResult.data !== undefined) {
          thenable.resolve(nextResult.data)
        }
      }

      /**
       * Create a new thenable and result promise when the results have changed
       */
      const recreateThenable = () => {
        const pending =
          (this.#currentThenable =
          nextResult.promise =
            pendingThenable())

        finalizeThenableIfPossible(pending)
      }

      const prevThenable = this.#currentThenable
      switch (prevThenable.status) {
        case 'pending':
          // Finalize the previous thenable if it was pending
          // and we are still observing the same query
          if (query.queryHash === prevQuery.queryHash) {
            finalizeThenableIfPossible(prevThenable)
          }
          break
        case 'fulfilled':
          if (
            nextResult.status === 'error' ||
            nextResult.data !== prevThenable.value
          ) {
            recreateThenable()
          }
          break
        case 'rejected':
          if (
            nextResult.status !== 'error' ||
            nextResult.error !== prevThenable.reason
          ) {
            recreateThenable()
          }
          break
      }
    }

    return nextResult
  }

  updateResult(): void {
    const prevResult = this.#currentResult as
      | QueryObserverResult<TData, TError>
      | undefined

    const nextResult = this.createResult(this.#currentQuery, this.options)

    this.#currentResultState = this.#currentQuery.state
    this.#currentResultOptions = this.options

    if (this.#currentResultState.data !== undefined) {
      this.#lastQueryWithDefinedData = this.#currentQuery
    }

    // Only notify and update result if something has changed
    if (shallowEqualObjects(nextResult, prevResult)) {
      return
    }

    this.#currentResult = nextResult

    const shouldNotifyListeners = (): boolean => {
      if (!prevResult) {
        return true
      }

      const { notifyOnChangeProps } = this.options
      const notifyOnChangePropsValue =
        typeof notifyOnChangeProps === 'function'
          ? notifyOnChangeProps()
          : notifyOnChangeProps

      if (
        notifyOnChangePropsValue === 'all' ||
        (!notifyOnChangePropsValue && !this.#trackedProps.size)
      ) {
        return true
      }

      const includedProps = new Set(
        notifyOnChangePropsValue ?? this.#trackedProps,
      )

      if (this.options.throwOnError) {
        includedProps.add('error')
      }

      return Object.keys(this.#currentResult).some((key) => {
        const typedKey = key as keyof QueryObserverResult
        const changed = this.#currentResult[typedKey] !== prevResult[typedKey]

        return changed && includedProps.has(typedKey)
      })
    }

    this.#notify({ listeners: shouldNotifyListeners() })
  }

  #updateQuery(): void {
    const query = this.#client.getQueryCache().build(this.#client, this.options)

    if (query === this.#currentQuery) {
      return
    }

    const prevQuery = this.#currentQuery as
      | Query<TQueryFnData, TError, TQueryData, TQueryKey>
      | undefined
    this.#currentQuery = query
    this.#currentQueryInitialState = query.state

    if (this.hasListeners()) {
      prevQuery?.removeObserver(this)
      query.addObserver(this)
    }
  }

  onQueryUpdate(): void {
    this.updateResult()

    if (this.hasListeners()) {
      this.#updateTimers()
    }
  }

  #notify(notifyOptions: { listeners: boolean }): void {
    notifyManager.batch(() => {
      // First, trigger the listeners
      if (notifyOptions.listeners) {
        this.listeners.forEach((listener) => {
          listener(this.#currentResult)
        })
      }

      // Then the cache listeners
      this.#client.getQueryCache().notify({
        query: this.#currentQuery,
        type: 'observerResultsUpdated',
      })
    })
  }
}

function shouldLoadOnMount(
  query: Query<any, any, any, any>,
  options: QueryObserverOptions<any, any, any, any>,
): boolean {
  return (
    resolveEnabled(options.enabled, query) !== false &&
    query.state.data === undefined &&
    !(query.state.status === 'error' && options.retryOnMount === false)
  )
}

function shouldFetchOnMount(
  query: Query<any, any, any, any>,
  options: QueryObserverOptions<any, any, any, any, any>,
): boolean {
  return (
    shouldLoadOnMount(query, options) ||
    (query.state.data !== undefined &&
      shouldFetchOn(query, options, options.refetchOnMount))
  )
}

function shouldFetchOn(
  query: Query<any, any, any, any>,
  options: QueryObserverOptions<any, any, any, any, any>,
  field: (typeof options)['refetchOnMount'] &
    (typeof options)['refetchOnWindowFocus'] &
    (typeof options)['refetchOnReconnect'],
) {
  if (
    resolveEnabled(options.enabled, query) !== false &&
    resolveStaleTime(options.staleTime, query) !== 'static'
  ) {
    const value = typeof field === 'function' ? field(query) : field

    return value === 'always' || (value !== false && isStale(query, options))
  }
  return false
}

function shouldFetchOptionally(
  query: Query<any, any, any, any>,
  prevQuery: Query<any, any, any, any>,
  options: QueryObserverOptions<any, any, any, any, any>,
  prevOptions: QueryObserverOptions<any, any, any, any, any>,
): boolean {
  return (
    (query !== prevQuery ||
      resolveEnabled(prevOptions.enabled, query) === false) &&
    (!options.suspense || query.state.status !== 'error') &&
    isStale(query, options)
  )
}

function isStale(
  query: Query<any, any, any, any>,
  options: QueryObserverOptions<any, any, any, any, any>,
): boolean {
  return (
    resolveEnabled(options.enabled, query) !== false &&
    query.isStaleByTime(resolveStaleTime(options.staleTime, query))
  )
}

// this function would decide if we will update the observer's 'current'
// properties after an optimistic reading via getOptimisticResult
function shouldAssignObserverCurrentProperties<
  TQueryFnData = unknown,
  TError = unknown,
  TData = TQueryFnData,
  TQueryData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
>(
  observer: QueryObserver<TQueryFnData, TError, TData, TQueryData, TQueryKey>,
  optimisticResult: QueryObserverResult<TData, TError>,
) {
  // if the newly created result isn't what the observer is holding as current,
  // then we'll need to update the properties as well
  if (!shallowEqualObjects(observer.getCurrentResult(), optimisticResult)) {
    return true
  }

  // basically, just keep previous properties if nothing changed
  return false
}
