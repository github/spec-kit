import {
  ensureQueryFn,
  noop,
  replaceData,
  resolveEnabled,
  resolveStaleTime,
  skipToken,
  timeUntilStale,
} from './utils'
import { notifyManager } from './notifyManager'
import { CancelledError, canFetch, createRetryer } from './retryer'
import { Removable } from './removable'
import type { QueryCache } from './queryCache'
import type { QueryClient } from './queryClient'
import type {
  CancelOptions,
  DefaultError,
  FetchStatus,
  InitialDataFunction,
  OmitKeyof,
  QueryFunctionContext,
  QueryKey,
  QueryMeta,
  QueryOptions,
  QueryStatus,
  SetDataOptions,
  StaleTime,
} from './types'
import type { QueryObserver } from './queryObserver'
import type { Retryer } from './retryer'

// TYPES

interface QueryConfig<
  TQueryFnData,
  TError,
  TData,
  TQueryKey extends QueryKey = QueryKey,
> {
  client: QueryClient
  queryKey: TQueryKey
  queryHash: string
  options?: QueryOptions<TQueryFnData, TError, TData, TQueryKey>
  defaultOptions?: QueryOptions<TQueryFnData, TError, TData, TQueryKey>
  state?: QueryState<TData, TError>
}

export interface QueryState<TData = unknown, TError = DefaultError> {
  data: TData | undefined
  dataUpdateCount: number
  dataUpdatedAt: number
  error: TError | null
  errorUpdateCount: number
  errorUpdatedAt: number
  fetchFailureCount: number
  fetchFailureReason: TError | null
  fetchMeta: FetchMeta | null
  isInvalidated: boolean
  status: QueryStatus
  fetchStatus: FetchStatus
}

export interface FetchContext<
  TQueryFnData,
  TError,
  TData,
  TQueryKey extends QueryKey = QueryKey,
> {
  fetchFn: () => unknown | Promise<unknown>
  fetchOptions?: FetchOptions
  signal: AbortSignal
  options: QueryOptions<TQueryFnData, TError, TData, any>
  client: QueryClient
  queryKey: TQueryKey
  state: QueryState<TData, TError>
}

export interface QueryBehavior<
  TQueryFnData = unknown,
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
> {
  onFetch: (
    context: FetchContext<TQueryFnData, TError, TData, TQueryKey>,
    query: Query,
  ) => void
}

export type FetchDirection = 'forward' | 'backward'

export interface FetchMeta {
  fetchMore?: { direction: FetchDirection }
}

export interface FetchOptions<TData = unknown> {
  cancelRefetch?: boolean
  meta?: FetchMeta
  initialPromise?: Promise<TData>
}

interface FailedAction<TError> {
  type: 'failed'
  failureCount: number
  error: TError
}

interface FetchAction {
  type: 'fetch'
  meta?: FetchMeta
}

interface SuccessAction<TData> {
  data: TData | undefined
  type: 'success'
  dataUpdatedAt?: number
  manual?: boolean
}

interface ErrorAction<TError> {
  type: 'error'
  error: TError
}

interface InvalidateAction {
  type: 'invalidate'
}

interface PauseAction {
  type: 'pause'
}

interface ContinueAction {
  type: 'continue'
}

interface SetStateAction<TData, TError> {
  type: 'setState'
  state: Partial<QueryState<TData, TError>>
  setStateOptions?: SetStateOptions
}

export type Action<TData, TError> =
  | ContinueAction
  | ErrorAction<TError>
  | FailedAction<TError>
  | FetchAction
  | InvalidateAction
  | PauseAction
  | SetStateAction<TData, TError>
  | SuccessAction<TData>

export interface SetStateOptions {
  meta?: any
}

// CLASS

export class Query<
  TQueryFnData = unknown,
  TError = DefaultError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
> extends Removable {
  queryKey: TQueryKey
  queryHash: string
  options!: QueryOptions<TQueryFnData, TError, TData, TQueryKey>
  state: QueryState<TData, TError>

  #initialState: QueryState<TData, TError>
  #revertState?: QueryState<TData, TError>
  #cache: QueryCache
  #client: QueryClient
  #retryer?: Retryer<TData>
  observers: Array<QueryObserver<any, any, any, any, any>>
  #defaultOptions?: QueryOptions<TQueryFnData, TError, TData, TQueryKey>
  #abortSignalConsumed: boolean

  constructor(config: QueryConfig<TQueryFnData, TError, TData, TQueryKey>) {
    super()

    this.#abortSignalConsumed = false
    this.#defaultOptions = config.defaultOptions
    this.setOptions(config.options)
    this.observers = []
    this.#client = config.client
    this.#cache = this.#client.getQueryCache()
    this.queryKey = config.queryKey
    this.queryHash = config.queryHash
    this.#initialState = getDefaultState(this.options)
    this.state = config.state ?? this.#initialState
    this.scheduleGc()
  }
  get meta(): QueryMeta | undefined {
    return this.options.meta
  }

  get promise(): Promise<TData> | undefined {
    return this.#retryer?.promise
  }

  setOptions(
    options?: QueryOptions<TQueryFnData, TError, TData, TQueryKey>,
  ): void {
    this.options = { ...this.#defaultOptions, ...options }

    this.updateGcTime(this.options.gcTime)

    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
    if (this.state && this.state.data === undefined) {
      const defaultState = getDefaultState(this.options)
      if (defaultState.data !== undefined) {
        this.setData(defaultState.data, {
          updatedAt: defaultState.dataUpdatedAt,
          manual: true,
        })
        this.#initialState = defaultState
      }
    }
  }

  protected optionalRemove() {
    if (!this.observers.length && this.state.fetchStatus === 'idle') {
      this.#cache.remove(this)
    }
  }

  setData(
    newData: TData,
    options?: SetDataOptions & { manual: boolean },
  ): TData {
    const data = replaceData(this.state.data, newData, this.options)

    // Set data and mark it as cached
    this.#dispatch({
      data,
      type: 'success',
      dataUpdatedAt: options?.updatedAt,
      manual: options?.manual,
    })

    return data
  }

  setState(
    state: Partial<QueryState<TData, TError>>,
    setStateOptions?: SetStateOptions,
  ): void {
    this.#dispatch({ type: 'setState', state, setStateOptions })
  }

  cancel(options?: CancelOptions): Promise<void> {
    const promise = this.#retryer?.promise
    this.#retryer?.cancel(options)
    return promise ? promise.then(noop).catch(noop) : Promise.resolve()
  }

  destroy(): void {
    super.destroy()

    this.cancel({ silent: true })
  }

  reset(): void {
    this.destroy()
    this.setState(this.#initialState)
  }

  isActive(): boolean {
    return this.observers.some(
      (observer) => resolveEnabled(observer.options.enabled, this) !== false,
    )
  }

  isDisabled(): boolean {
    if (this.getObserversCount() > 0) {
      return !this.isActive()
    }
    // if a query has no observers, it should still be considered disabled if it never attempted a fetch
    return (
      this.options.queryFn === skipToken ||
      this.state.dataUpdateCount + this.state.errorUpdateCount === 0
    )
  }

  isStatic(): boolean {
    if (this.getObserversCount() > 0) {
      return this.observers.some(
        (observer) =>
          resolveStaleTime(observer.options.staleTime, this) === 'static',
      )
    }

    return false
  }

  isStale(): boolean {
    // check observers first, their `isStale` has the source of truth
    // calculated with `isStaleByTime` and it takes `enabled` into account
    if (this.getObserversCount() > 0) {
      return this.observers.some(
        (observer) => observer.getCurrentResult().isStale,
      )
    }

    return this.state.data === undefined || this.state.isInvalidated
  }

  isStaleByTime(staleTime: StaleTime = 0): boolean {
    // no data is always stale
    if (this.state.data === undefined) {
      return true
    }
    // static is never stale
    if (staleTime === 'static') {
      return false
    }
    // if the query is invalidated, it is stale
    if (this.state.isInvalidated) {
      return true
    }

    return !timeUntilStale(this.state.dataUpdatedAt, staleTime)
  }

  onFocus(): void {
    const observer = this.observers.find((x) => x.shouldFetchOnWindowFocus())

    observer?.refetch({ cancelRefetch: false })

    // Continue fetch if currently paused
    this.#retryer?.continue()
  }

  onOnline(): void {
    const observer = this.observers.find((x) => x.shouldFetchOnReconnect())

    observer?.refetch({ cancelRefetch: false })

    // Continue fetch if currently paused
    this.#retryer?.continue()
  }

  addObserver(observer: QueryObserver<any, any, any, any, any>): void {
    if (!this.observers.includes(observer)) {
      this.observers.push(observer)

      // Stop the query from being garbage collected
      this.clearGcTimeout()

      this.#cache.notify({ type: 'observerAdded', query: this, observer })
    }
  }

  removeObserver(observer: QueryObserver<any, any, any, any, any>): void {
    if (this.observers.includes(observer)) {
      this.observers = this.observers.filter((x) => x !== observer)

      if (!this.observers.length) {
        // If the transport layer does not support cancellation
        // we'll let the query continue so the result can be cached
        if (this.#retryer) {
          if (this.#abortSignalConsumed) {
            this.#retryer.cancel({ revert: true })
          } else {
            this.#retryer.cancelRetry()
          }
        }

        this.scheduleGc()
      }

      this.#cache.notify({ type: 'observerRemoved', query: this, observer })
    }
  }

  getObserversCount(): number {
    return this.observers.length
  }

  invalidate(): void {
    if (!this.state.isInvalidated) {
      this.#dispatch({ type: 'invalidate' })
    }
  }

  async fetch(
    options?: QueryOptions<TQueryFnData, TError, TData, TQueryKey>,
    fetchOptions?: FetchOptions<TQueryFnData>,
  ): Promise<TData> {
    if (
      this.state.fetchStatus !== 'idle' &&
      // If the promise in the retyer is already rejected, we have to definitely
      // re-start the fetch; there is a chance that the query is still in a
      // pending state when that happens
      this.#retryer?.status() !== 'rejected'
    ) {
      if (this.state.data !== undefined && fetchOptions?.cancelRefetch) {
        // Silently cancel current fetch if the user wants to cancel refetch
        this.cancel({ silent: true })
      } else if (this.#retryer) {
        // make sure that retries that were potentially cancelled due to unmounts can continue
        this.#retryer.continueRetry()
        // Return current promise if we are already fetching
        return this.#retryer.promise
      }
    }

    // Update config if passed, otherwise the config from the last execution is used
    if (options) {
      this.setOptions(options)
    }

    // Use the options from the first observer with a query function if no function is found.
    // This can happen when the query is hydrated or created with setQueryData.
    if (!this.options.queryFn) {
      const observer = this.observers.find((x) => x.options.queryFn)
      if (observer) {
        this.setOptions(observer.options)
      }
    }

    if (process.env.NODE_ENV !== 'production') {
      if (!Array.isArray(this.options.queryKey)) {
        console.error(
          `As of v4, queryKey needs to be an Array. If you are using a string like 'repoData', please change it to an Array, e.g. ['repoData']`,
        )
      }
    }

    const abortController = new AbortController()

    // Adds an enumerable signal property to the object that
    // which sets abortSignalConsumed to true when the signal
    // is read.
    const addSignalProperty = (object: unknown) => {
      Object.defineProperty(object, 'signal', {
        enumerable: true,
        get: () => {
          this.#abortSignalConsumed = true
          return abortController.signal
        },
      })
    }

    // Create fetch function
    const fetchFn = () => {
      const queryFn = ensureQueryFn(this.options, fetchOptions)

      // Create query function context
      const createQueryFnContext = (): QueryFunctionContext<TQueryKey> => {
        const queryFnContext: OmitKeyof<
          QueryFunctionContext<TQueryKey>,
          'signal'
        > = {
          client: this.#client,
          queryKey: this.queryKey,
          meta: this.meta,
        }
        addSignalProperty(queryFnContext)
        return queryFnContext as QueryFunctionContext<TQueryKey>
      }

      const queryFnContext = createQueryFnContext()

      this.#abortSignalConsumed = false
      if (this.options.persister) {
        return this.options.persister(
          queryFn,
          queryFnContext,
          this as unknown as Query,
        )
      }

      return queryFn(queryFnContext)
    }

    // Trigger behavior hook
    const createFetchContext = (): FetchContext<
      TQueryFnData,
      TError,
      TData,
      TQueryKey
    > => {
      const context: OmitKeyof<
        FetchContext<TQueryFnData, TError, TData, TQueryKey>,
        'signal'
      > = {
        fetchOptions,
        options: this.options,
        queryKey: this.queryKey,
        client: this.#client,
        state: this.state,
        fetchFn,
      }

      addSignalProperty(context)
      return context as FetchContext<TQueryFnData, TError, TData, TQueryKey>
    }

    const context = createFetchContext()

    this.options.behavior?.onFetch(context, this as unknown as Query)

    // Store state in case the current fetch needs to be reverted
    this.#revertState = this.state

    // Set to fetching state if not already in it
    if (
      this.state.fetchStatus === 'idle' ||
      this.state.fetchMeta !== context.fetchOptions?.meta
    ) {
      this.#dispatch({ type: 'fetch', meta: context.fetchOptions?.meta })
    }

    // Try to fetch the data
    this.#retryer = createRetryer({
      initialPromise: fetchOptions?.initialPromise as
        | Promise<TData>
        | undefined,
      fn: context.fetchFn as () => Promise<TData>,
      onCancel: (error) => {
        if (error instanceof CancelledError && error.revert) {
          this.setState({
            ...this.#revertState,
            fetchStatus: 'idle' as const,
          })
        }
        abortController.abort()
      },
      onFail: (failureCount, error) => {
        this.#dispatch({ type: 'failed', failureCount, error })
      },
      onPause: () => {
        this.#dispatch({ type: 'pause' })
      },
      onContinue: () => {
        this.#dispatch({ type: 'continue' })
      },
      retry: context.options.retry,
      retryDelay: context.options.retryDelay,
      networkMode: context.options.networkMode,
      canRun: () => true,
    })

    try {
      const data = await this.#retryer.start()
      // this is more of a runtime guard
      // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
      if (data === undefined) {
        if (process.env.NODE_ENV !== 'production') {
          console.error(
            `Query data cannot be undefined. Please make sure to return a value other than undefined from your query function. Affected query key: ${this.queryHash}`,
          )
        }
        throw new Error(`${this.queryHash} data is undefined`)
      }

      this.setData(data)

      // Notify cache callback
      this.#cache.config.onSuccess?.(data, this as Query<any, any, any, any>)
      this.#cache.config.onSettled?.(
        data,
        this.state.error as any,
        this as Query<any, any, any, any>,
      )
      return data
    } catch (error) {
      if (error instanceof CancelledError) {
        if (error.silent) {
          // silent cancellation implies a new fetch is going to be started,
          // so we piggyback onto that promise
          return this.#retryer.promise
        } else if (error.revert) {
          // transform error into reverted state data
          // if the initial fetch was cancelled, we have no data, so we have
          // to get reject with a CancelledError
          if (this.state.data === undefined) {
            throw error
          }
          return this.state.data
        }
      }
      this.#dispatch({
        type: 'error',
        error: error as TError,
      })

      // Notify cache callback
      this.#cache.config.onError?.(
        error as any,
        this as Query<any, any, any, any>,
      )
      this.#cache.config.onSettled?.(
        this.state.data,
        error as any,
        this as Query<any, any, any, any>,
      )

      throw error // rethrow the error for further handling
    } finally {
      // Schedule query gc after fetching
      this.scheduleGc()
    }
  }

  #dispatch(action: Action<TData, TError>): void {
    const reducer = (
      state: QueryState<TData, TError>,
    ): QueryState<TData, TError> => {
      switch (action.type) {
        case 'failed':
          return {
            ...state,
            fetchFailureCount: action.failureCount,
            fetchFailureReason: action.error,
          }
        case 'pause':
          return {
            ...state,
            fetchStatus: 'paused',
          }
        case 'continue':
          return {
            ...state,
            fetchStatus: 'fetching',
          }
        case 'fetch':
          return {
            ...state,
            ...fetchState(state.data, this.options),
            fetchMeta: action.meta ?? null,
          }
        case 'success':
          const newState = {
            ...state,
            data: action.data,
            dataUpdateCount: state.dataUpdateCount + 1,
            dataUpdatedAt: action.dataUpdatedAt ?? Date.now(),
            error: null,
            isInvalidated: false,
            status: 'success' as const,
            ...(!action.manual && {
              fetchStatus: 'idle' as const,
              fetchFailureCount: 0,
              fetchFailureReason: null,
            }),
          }
          // If fetching ends successfully, we don't need revertState as a fallback anymore.
          // For manual updates, capture the state to revert to it in case of a cancellation.
          this.#revertState = action.manual ? newState : undefined

          return newState
        case 'error':
          const error = action.error
          return {
            ...state,
            error,
            errorUpdateCount: state.errorUpdateCount + 1,
            errorUpdatedAt: Date.now(),
            fetchFailureCount: state.fetchFailureCount + 1,
            fetchFailureReason: error,
            fetchStatus: 'idle',
            status: 'error',
          }
        case 'invalidate':
          return {
            ...state,
            isInvalidated: true,
          }
        case 'setState':
          return {
            ...state,
            ...action.state,
          }
      }
    }

    this.state = reducer(this.state)

    notifyManager.batch(() => {
      this.observers.forEach((observer) => {
        observer.onQueryUpdate()
      })

      this.#cache.notify({ query: this, type: 'updated', action })
    })
  }
}

export function fetchState<
  TQueryFnData,
  TError,
  TData,
  TQueryKey extends QueryKey,
>(
  data: TData | undefined,
  options: QueryOptions<TQueryFnData, TError, TData, TQueryKey>,
) {
  return {
    fetchFailureCount: 0,
    fetchFailureReason: null,
    fetchStatus: canFetch(options.networkMode) ? 'fetching' : 'paused',
    ...(data === undefined &&
      ({
        error: null,
        status: 'pending',
      } as const)),
  } as const
}

function getDefaultState<
  TQueryFnData,
  TError,
  TData,
  TQueryKey extends QueryKey,
>(
  options: QueryOptions<TQueryFnData, TError, TData, TQueryKey>,
): QueryState<TData, TError> {
  const data =
    typeof options.initialData === 'function'
      ? (options.initialData as InitialDataFunction<TData>)()
      : options.initialData

  const hasData = data !== undefined

  const initialDataUpdatedAt = hasData
    ? typeof options.initialDataUpdatedAt === 'function'
      ? (options.initialDataUpdatedAt as () => number | undefined)()
      : options.initialDataUpdatedAt
    : 0

  return {
    data,
    dataUpdateCount: 0,
    dataUpdatedAt: hasData ? (initialDataUpdatedAt ?? Date.now()) : 0,
    error: null,
    errorUpdateCount: 0,
    errorUpdatedAt: 0,
    fetchFailureCount: 0,
    fetchFailureReason: null,
    fetchMeta: null,
    isInvalidated: false,
    status: hasData ? 'success' : 'pending',
    fetchStatus: 'idle',
  }
}
