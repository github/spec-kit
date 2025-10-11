import { Removable } from './removable.cjs';
import { Subscribable } from './subscribable.cjs';

type QueryObserverListener<TData, TError> = (result: QueryObserverResult<TData, TError>) => void;
interface ObserverFetchOptions extends FetchOptions {
    throwOnError?: boolean;
}
declare class QueryObserver<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryData = TQueryFnData, TQueryKey extends QueryKey = QueryKey> extends Subscribable<QueryObserverListener<TData, TError>> {
    #private;
    options: QueryObserverOptions<TQueryFnData, TError, TData, TQueryData, TQueryKey>;
    constructor(client: QueryClient, options: QueryObserverOptions<TQueryFnData, TError, TData, TQueryData, TQueryKey>);
    protected bindMethods(): void;
    protected onSubscribe(): void;
    protected onUnsubscribe(): void;
    shouldFetchOnReconnect(): boolean;
    shouldFetchOnWindowFocus(): boolean;
    destroy(): void;
    setOptions(options: QueryObserverOptions<TQueryFnData, TError, TData, TQueryData, TQueryKey>): void;
    getOptimisticResult(options: DefaultedQueryObserverOptions<TQueryFnData, TError, TData, TQueryData, TQueryKey>): QueryObserverResult<TData, TError>;
    getCurrentResult(): QueryObserverResult<TData, TError>;
    trackResult(result: QueryObserverResult<TData, TError>, onPropTracked?: (key: keyof QueryObserverResult) => void): QueryObserverResult<TData, TError>;
    trackProp(key: keyof QueryObserverResult): void;
    getCurrentQuery(): Query<TQueryFnData, TError, TQueryData, TQueryKey>;
    refetch({ ...options }?: RefetchOptions): Promise<QueryObserverResult<TData, TError>>;
    fetchOptimistic(options: QueryObserverOptions<TQueryFnData, TError, TData, TQueryData, TQueryKey>): Promise<QueryObserverResult<TData, TError>>;
    protected fetch(fetchOptions: ObserverFetchOptions): Promise<QueryObserverResult<TData, TError>>;
    protected createResult(query: Query<TQueryFnData, TError, TQueryData, TQueryKey>, options: QueryObserverOptions<TQueryFnData, TError, TData, TQueryData, TQueryKey>): QueryObserverResult<TData, TError>;
    updateResult(): void;
    onQueryUpdate(): void;
}

interface QueryConfig<TQueryFnData, TError, TData, TQueryKey extends QueryKey = QueryKey> {
    client: QueryClient;
    queryKey: TQueryKey;
    queryHash: string;
    options?: QueryOptions<TQueryFnData, TError, TData, TQueryKey>;
    defaultOptions?: QueryOptions<TQueryFnData, TError, TData, TQueryKey>;
    state?: QueryState<TData, TError>;
}
interface QueryState<TData = unknown, TError = DefaultError> {
    data: TData | undefined;
    dataUpdateCount: number;
    dataUpdatedAt: number;
    error: TError | null;
    errorUpdateCount: number;
    errorUpdatedAt: number;
    fetchFailureCount: number;
    fetchFailureReason: TError | null;
    fetchMeta: FetchMeta | null;
    isInvalidated: boolean;
    status: QueryStatus;
    fetchStatus: FetchStatus;
}
interface FetchContext<TQueryFnData, TError, TData, TQueryKey extends QueryKey = QueryKey> {
    fetchFn: () => unknown | Promise<unknown>;
    fetchOptions?: FetchOptions;
    signal: AbortSignal;
    options: QueryOptions<TQueryFnData, TError, TData, any>;
    client: QueryClient;
    queryKey: TQueryKey;
    state: QueryState<TData, TError>;
}
interface QueryBehavior<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey> {
    onFetch: (context: FetchContext<TQueryFnData, TError, TData, TQueryKey>, query: Query) => void;
}
type FetchDirection = 'forward' | 'backward';
interface FetchMeta {
    fetchMore?: {
        direction: FetchDirection;
    };
}
interface FetchOptions<TData = unknown> {
    cancelRefetch?: boolean;
    meta?: FetchMeta;
    initialPromise?: Promise<TData>;
}
interface FailedAction$1<TError> {
    type: 'failed';
    failureCount: number;
    error: TError;
}
interface FetchAction {
    type: 'fetch';
    meta?: FetchMeta;
}
interface SuccessAction$1<TData> {
    data: TData | undefined;
    type: 'success';
    dataUpdatedAt?: number;
    manual?: boolean;
}
interface ErrorAction$1<TError> {
    type: 'error';
    error: TError;
}
interface InvalidateAction {
    type: 'invalidate';
}
interface PauseAction$1 {
    type: 'pause';
}
interface ContinueAction$1 {
    type: 'continue';
}
interface SetStateAction<TData, TError> {
    type: 'setState';
    state: Partial<QueryState<TData, TError>>;
    setStateOptions?: SetStateOptions;
}
type Action$1<TData, TError> = ContinueAction$1 | ErrorAction$1<TError> | FailedAction$1<TError> | FetchAction | InvalidateAction | PauseAction$1 | SetStateAction<TData, TError> | SuccessAction$1<TData>;
interface SetStateOptions {
    meta?: any;
}
declare class Query<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey> extends Removable {
    #private;
    queryKey: TQueryKey;
    queryHash: string;
    options: QueryOptions<TQueryFnData, TError, TData, TQueryKey>;
    state: QueryState<TData, TError>;
    observers: Array<QueryObserver<any, any, any, any, any>>;
    constructor(config: QueryConfig<TQueryFnData, TError, TData, TQueryKey>);
    get meta(): QueryMeta | undefined;
    get promise(): Promise<TData> | undefined;
    setOptions(options?: QueryOptions<TQueryFnData, TError, TData, TQueryKey>): void;
    protected optionalRemove(): void;
    setData(newData: TData, options?: SetDataOptions & {
        manual: boolean;
    }): TData;
    setState(state: Partial<QueryState<TData, TError>>, setStateOptions?: SetStateOptions): void;
    cancel(options?: CancelOptions): Promise<void>;
    destroy(): void;
    reset(): void;
    isActive(): boolean;
    isDisabled(): boolean;
    isStatic(): boolean;
    isStale(): boolean;
    isStaleByTime(staleTime?: StaleTime): boolean;
    onFocus(): void;
    onOnline(): void;
    addObserver(observer: QueryObserver<any, any, any, any, any>): void;
    removeObserver(observer: QueryObserver<any, any, any, any, any>): void;
    getObserversCount(): number;
    invalidate(): void;
    fetch(options?: QueryOptions<TQueryFnData, TError, TData, TQueryKey>, fetchOptions?: FetchOptions<TQueryFnData>): Promise<TData>;
}
declare function fetchState<TQueryFnData, TError, TData, TQueryKey extends QueryKey>(data: TData | undefined, options: QueryOptions<TQueryFnData, TError, TData, TQueryKey>): {
    readonly error?: null | undefined;
    readonly status?: "pending" | undefined;
    readonly fetchFailureCount: 0;
    readonly fetchFailureReason: null;
    readonly fetchStatus: "fetching" | "paused";
};

type MutationObserverListener<TData, TError, TVariables, TOnMutateResult> = (result: MutationObserverResult<TData, TError, TVariables, TOnMutateResult>) => void;
declare class MutationObserver<TData = unknown, TError = DefaultError, TVariables = void, TOnMutateResult = unknown> extends Subscribable<MutationObserverListener<TData, TError, TVariables, TOnMutateResult>> {
    #private;
    options: MutationObserverOptions<TData, TError, TVariables, TOnMutateResult>;
    constructor(client: QueryClient, options: MutationObserverOptions<TData, TError, TVariables, TOnMutateResult>);
    protected bindMethods(): void;
    setOptions(options: MutationObserverOptions<TData, TError, TVariables, TOnMutateResult>): void;
    protected onUnsubscribe(): void;
    onMutationUpdate(action: Action<TData, TError, TVariables, TOnMutateResult>): void;
    getCurrentResult(): MutationObserverResult<TData, TError, TVariables, TOnMutateResult>;
    reset(): void;
    mutate(variables: TVariables, options?: MutateOptions<TData, TError, TVariables, TOnMutateResult>): Promise<TData>;
}

interface MutationCacheConfig {
    onError?: (error: DefaultError, variables: unknown, onMutateResult: unknown, mutation: Mutation<unknown, unknown, unknown>, context: MutationFunctionContext) => Promise<unknown> | unknown;
    onSuccess?: (data: unknown, variables: unknown, onMutateResult: unknown, mutation: Mutation<unknown, unknown, unknown>, context: MutationFunctionContext) => Promise<unknown> | unknown;
    onMutate?: (variables: unknown, mutation: Mutation<unknown, unknown, unknown>, context: MutationFunctionContext) => Promise<unknown> | unknown;
    onSettled?: (data: unknown | undefined, error: DefaultError | null, variables: unknown, onMutateResult: unknown, mutation: Mutation<unknown, unknown, unknown>, context: MutationFunctionContext) => Promise<unknown> | unknown;
}
interface NotifyEventMutationAdded extends NotifyEvent {
    type: 'added';
    mutation: Mutation<any, any, any, any>;
}
interface NotifyEventMutationRemoved extends NotifyEvent {
    type: 'removed';
    mutation: Mutation<any, any, any, any>;
}
interface NotifyEventMutationObserverAdded extends NotifyEvent {
    type: 'observerAdded';
    mutation: Mutation<any, any, any, any>;
    observer: MutationObserver<any, any, any>;
}
interface NotifyEventMutationObserverRemoved extends NotifyEvent {
    type: 'observerRemoved';
    mutation: Mutation<any, any, any, any>;
    observer: MutationObserver<any, any, any>;
}
interface NotifyEventMutationObserverOptionsUpdated extends NotifyEvent {
    type: 'observerOptionsUpdated';
    mutation?: Mutation<any, any, any, any>;
    observer: MutationObserver<any, any, any, any>;
}
interface NotifyEventMutationUpdated extends NotifyEvent {
    type: 'updated';
    mutation: Mutation<any, any, any, any>;
    action: Action<any, any, any, any>;
}
type MutationCacheNotifyEvent = NotifyEventMutationAdded | NotifyEventMutationRemoved | NotifyEventMutationObserverAdded | NotifyEventMutationObserverRemoved | NotifyEventMutationObserverOptionsUpdated | NotifyEventMutationUpdated;
type MutationCacheListener = (event: MutationCacheNotifyEvent) => void;
declare class MutationCache extends Subscribable<MutationCacheListener> {
    #private;
    config: MutationCacheConfig;
    constructor(config?: MutationCacheConfig);
    build<TData, TError, TVariables, TOnMutateResult>(client: QueryClient, options: MutationOptions<TData, TError, TVariables, TOnMutateResult>, state?: MutationState<TData, TError, TVariables, TOnMutateResult>): Mutation<TData, TError, TVariables, TOnMutateResult>;
    add(mutation: Mutation<any, any, any, any>): void;
    remove(mutation: Mutation<any, any, any, any>): void;
    canRun(mutation: Mutation<any, any, any, any>): boolean;
    runNext(mutation: Mutation<any, any, any, any>): Promise<unknown>;
    clear(): void;
    getAll(): Array<Mutation>;
    find<TData = unknown, TError = DefaultError, TVariables = any, TOnMutateResult = unknown>(filters: MutationFilters): Mutation<TData, TError, TVariables, TOnMutateResult> | undefined;
    findAll(filters?: MutationFilters): Array<Mutation>;
    notify(event: MutationCacheNotifyEvent): void;
    resumePausedMutations(): Promise<unknown>;
}

interface MutationConfig<TData, TError, TVariables, TOnMutateResult> {
    client: QueryClient;
    mutationId: number;
    mutationCache: MutationCache;
    options: MutationOptions<TData, TError, TVariables, TOnMutateResult>;
    state?: MutationState<TData, TError, TVariables, TOnMutateResult>;
}
interface MutationState<TData = unknown, TError = DefaultError, TVariables = unknown, TOnMutateResult = unknown> {
    context: TOnMutateResult | undefined;
    data: TData | undefined;
    error: TError | null;
    failureCount: number;
    failureReason: TError | null;
    isPaused: boolean;
    status: MutationStatus;
    variables: TVariables | undefined;
    submittedAt: number;
}
interface FailedAction<TError> {
    type: 'failed';
    failureCount: number;
    error: TError | null;
}
interface PendingAction<TVariables, TOnMutateResult> {
    type: 'pending';
    isPaused: boolean;
    variables?: TVariables;
    context?: TOnMutateResult;
}
interface SuccessAction<TData> {
    type: 'success';
    data: TData;
}
interface ErrorAction<TError> {
    type: 'error';
    error: TError;
}
interface PauseAction {
    type: 'pause';
}
interface ContinueAction {
    type: 'continue';
}
type Action<TData, TError, TVariables, TOnMutateResult> = ContinueAction | ErrorAction<TError> | FailedAction<TError> | PendingAction<TVariables, TOnMutateResult> | PauseAction | SuccessAction<TData>;
declare class Mutation<TData = unknown, TError = DefaultError, TVariables = unknown, TOnMutateResult = unknown> extends Removable {
    #private;
    state: MutationState<TData, TError, TVariables, TOnMutateResult>;
    options: MutationOptions<TData, TError, TVariables, TOnMutateResult>;
    readonly mutationId: number;
    constructor(config: MutationConfig<TData, TError, TVariables, TOnMutateResult>);
    setOptions(options: MutationOptions<TData, TError, TVariables, TOnMutateResult>): void;
    get meta(): MutationMeta | undefined;
    addObserver(observer: MutationObserver<any, any, any, any>): void;
    removeObserver(observer: MutationObserver<any, any, any, any>): void;
    protected optionalRemove(): void;
    continue(): Promise<unknown>;
    execute(variables: TVariables): Promise<TData>;
}
declare function getDefaultState<TData, TError, TVariables, TOnMutateResult>(): MutationState<TData, TError, TVariables, TOnMutateResult>;

interface QueryFilters<TQueryKey extends QueryKey = QueryKey> {
    /**
     * Filter to active queries, inactive queries or all queries
     */
    type?: QueryTypeFilter;
    /**
     * Match query key exactly
     */
    exact?: boolean;
    /**
     * Include queries matching this predicate function
     */
    predicate?: (query: Query) => boolean;
    /**
     * Include queries matching this query key
     */
    queryKey?: TQueryKey;
    /**
     * Include or exclude stale queries
     */
    stale?: boolean;
    /**
     * Include queries matching their fetchStatus
     */
    fetchStatus?: FetchStatus;
}
interface MutationFilters<TData = unknown, TError = DefaultError, TVariables = unknown, TOnMutateResult = unknown> {
    /**
     * Match mutation key exactly
     */
    exact?: boolean;
    /**
     * Include mutations matching this predicate function
     */
    predicate?: (mutation: Mutation<TData, TError, TVariables, TOnMutateResult>) => boolean;
    /**
     * Include mutations matching this mutation key
     */
    mutationKey?: MutationKey;
    /**
     * Filter by mutation status
     */
    status?: MutationStatus;
}
type Updater<TInput, TOutput> = TOutput | ((input: TInput) => TOutput);
type QueryTypeFilter = 'all' | 'active' | 'inactive';
declare const isServer: boolean;
declare function noop(): void;
declare function noop(): undefined;
declare function functionalUpdate<TInput, TOutput>(updater: Updater<TInput, TOutput>, input: TInput): TOutput;
declare function isValidTimeout(value: unknown): value is number;
declare function timeUntilStale(updatedAt: number, staleTime?: number): number;
declare function resolveStaleTime<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey>(staleTime: undefined | StaleTimeFunction<TQueryFnData, TError, TData, TQueryKey>, query: Query<TQueryFnData, TError, TData, TQueryKey>): StaleTime | undefined;
declare function resolveEnabled<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey>(enabled: undefined | Enabled<TQueryFnData, TError, TData, TQueryKey>, query: Query<TQueryFnData, TError, TData, TQueryKey>): boolean | undefined;
declare function matchQuery(filters: QueryFilters, query: Query<any, any, any, any>): boolean;
declare function matchMutation(filters: MutationFilters, mutation: Mutation<any, any>): boolean;
declare function hashQueryKeyByOptions<TQueryKey extends QueryKey = QueryKey>(queryKey: TQueryKey, options?: Pick<QueryOptions<any, any, any, any>, 'queryKeyHashFn'>): string;
/**
 * Default query & mutation keys hash function.
 * Hashes the value into a stable hash.
 */
declare function hashKey(queryKey: QueryKey | MutationKey): string;
/**
 * Checks if key `b` partially matches with key `a`.
 */
declare function partialMatchKey(a: QueryKey, b: QueryKey): boolean;
/**
 * This function returns `a` if `b` is deeply equal.
 * If not, it will replace any deeply equal children of `b` with those of `a`.
 * This can be used for structural sharing between JSON values for example.
 */
declare function replaceEqualDeep<T>(a: unknown, b: T): T;
/**
 * Shallow compare objects.
 */
declare function shallowEqualObjects<T extends Record<string, any>>(a: T, b: T | undefined): boolean;
declare function isPlainArray(value: unknown): value is Array<unknown>;
declare function isPlainObject(o: any): o is Record<PropertyKey, unknown>;
declare function sleep(timeout: number): Promise<void>;
declare function replaceData<TData, TOptions extends QueryOptions<any, any, any, any>>(prevData: TData | undefined, data: TData, options: TOptions): TData;
declare function keepPreviousData<T>(previousData: T | undefined): T | undefined;
declare function addToEnd<T>(items: Array<T>, item: T, max?: number): Array<T>;
declare function addToStart<T>(items: Array<T>, item: T, max?: number): Array<T>;
declare const skipToken: unique symbol;
type SkipToken = typeof skipToken;
declare function ensureQueryFn<TQueryFnData = unknown, TQueryKey extends QueryKey = QueryKey>(options: {
    queryFn?: QueryFunction<TQueryFnData, TQueryKey> | SkipToken;
    queryHash?: string;
}, fetchOptions?: FetchOptions<TQueryFnData>): QueryFunction<TQueryFnData, TQueryKey>;
declare function shouldThrowError<T extends (...args: Array<any>) => boolean>(throwOnError: boolean | T | undefined, params: Parameters<T>): boolean;

interface QueryCacheConfig {
    onError?: (error: DefaultError, query: Query<unknown, unknown, unknown>) => void;
    onSuccess?: (data: unknown, query: Query<unknown, unknown, unknown>) => void;
    onSettled?: (data: unknown | undefined, error: DefaultError | null, query: Query<unknown, unknown, unknown>) => void;
}
interface NotifyEventQueryAdded extends NotifyEvent {
    type: 'added';
    query: Query<any, any, any, any>;
}
interface NotifyEventQueryRemoved extends NotifyEvent {
    type: 'removed';
    query: Query<any, any, any, any>;
}
interface NotifyEventQueryUpdated extends NotifyEvent {
    type: 'updated';
    query: Query<any, any, any, any>;
    action: Action$1<any, any>;
}
interface NotifyEventQueryObserverAdded extends NotifyEvent {
    type: 'observerAdded';
    query: Query<any, any, any, any>;
    observer: QueryObserver<any, any, any, any, any>;
}
interface NotifyEventQueryObserverRemoved extends NotifyEvent {
    type: 'observerRemoved';
    query: Query<any, any, any, any>;
    observer: QueryObserver<any, any, any, any, any>;
}
interface NotifyEventQueryObserverResultsUpdated extends NotifyEvent {
    type: 'observerResultsUpdated';
    query: Query<any, any, any, any>;
}
interface NotifyEventQueryObserverOptionsUpdated extends NotifyEvent {
    type: 'observerOptionsUpdated';
    query: Query<any, any, any, any>;
    observer: QueryObserver<any, any, any, any, any>;
}
type QueryCacheNotifyEvent = NotifyEventQueryAdded | NotifyEventQueryRemoved | NotifyEventQueryUpdated | NotifyEventQueryObserverAdded | NotifyEventQueryObserverRemoved | NotifyEventQueryObserverResultsUpdated | NotifyEventQueryObserverOptionsUpdated;
type QueryCacheListener = (event: QueryCacheNotifyEvent) => void;
interface QueryStore {
    has: (queryHash: string) => boolean;
    set: (queryHash: string, query: Query) => void;
    get: (queryHash: string) => Query | undefined;
    delete: (queryHash: string) => void;
    values: () => IterableIterator<Query>;
}
declare class QueryCache extends Subscribable<QueryCacheListener> {
    #private;
    config: QueryCacheConfig;
    constructor(config?: QueryCacheConfig);
    build<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey>(client: QueryClient, options: WithRequired<QueryOptions<TQueryFnData, TError, TData, TQueryKey>, 'queryKey'>, state?: QueryState<TData, TError>): Query<TQueryFnData, TError, TData, TQueryKey>;
    add(query: Query<any, any, any, any>): void;
    remove(query: Query<any, any, any, any>): void;
    clear(): void;
    get<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey>(queryHash: string): Query<TQueryFnData, TError, TData, TQueryKey> | undefined;
    getAll(): Array<Query>;
    find<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData>(filters: WithRequired<QueryFilters, 'queryKey'>): Query<TQueryFnData, TError, TData> | undefined;
    findAll(filters?: QueryFilters<any>): Array<Query>;
    notify(event: QueryCacheNotifyEvent): void;
    onFocus(): void;
    onOnline(): void;
}

declare class QueryClient {
    #private;
    constructor(config?: QueryClientConfig);
    mount(): void;
    unmount(): void;
    isFetching<TQueryFilters extends QueryFilters<any> = QueryFilters>(filters?: TQueryFilters): number;
    isMutating<TMutationFilters extends MutationFilters<any, any> = MutationFilters>(filters?: TMutationFilters): number;
    /**
     * Imperative (non-reactive) way to retrieve data for a QueryKey.
     * Should only be used in callbacks or functions where reading the latest data is necessary, e.g. for optimistic updates.
     *
     * Hint: Do not use this function inside a component, because it won't receive updates.
     * Use `useQuery` to create a `QueryObserver` that subscribes to changes.
     */
    getQueryData<TQueryFnData = unknown, TTaggedQueryKey extends QueryKey = QueryKey, TInferredQueryFnData = InferDataFromTag<TQueryFnData, TTaggedQueryKey>>(queryKey: TTaggedQueryKey): TInferredQueryFnData | undefined;
    ensureQueryData<TQueryFnData, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey>(options: EnsureQueryDataOptions<TQueryFnData, TError, TData, TQueryKey>): Promise<TData>;
    getQueriesData<TQueryFnData = unknown, TQueryFilters extends QueryFilters<any> = QueryFilters>(filters: TQueryFilters): Array<[QueryKey, TQueryFnData | undefined]>;
    setQueryData<TQueryFnData = unknown, TTaggedQueryKey extends QueryKey = QueryKey, TInferredQueryFnData = InferDataFromTag<TQueryFnData, TTaggedQueryKey>>(queryKey: TTaggedQueryKey, updater: Updater<NoInfer<TInferredQueryFnData> | undefined, NoInfer<TInferredQueryFnData> | undefined>, options?: SetDataOptions): NoInfer<TInferredQueryFnData> | undefined;
    setQueriesData<TQueryFnData, TQueryFilters extends QueryFilters<any> = QueryFilters>(filters: TQueryFilters, updater: Updater<NoInfer<TQueryFnData> | undefined, NoInfer<TQueryFnData> | undefined>, options?: SetDataOptions): Array<[QueryKey, TQueryFnData | undefined]>;
    getQueryState<TQueryFnData = unknown, TError = DefaultError, TTaggedQueryKey extends QueryKey = QueryKey, TInferredQueryFnData = InferDataFromTag<TQueryFnData, TTaggedQueryKey>, TInferredError = InferErrorFromTag<TError, TTaggedQueryKey>>(queryKey: TTaggedQueryKey): QueryState<TInferredQueryFnData, TInferredError> | undefined;
    removeQueries<TTaggedQueryKey extends QueryKey = QueryKey>(filters?: QueryFilters<TTaggedQueryKey>): void;
    resetQueries<TTaggedQueryKey extends QueryKey = QueryKey>(filters?: QueryFilters<TTaggedQueryKey>, options?: ResetOptions): Promise<void>;
    cancelQueries<TTaggedQueryKey extends QueryKey = QueryKey>(filters?: QueryFilters<TTaggedQueryKey>, cancelOptions?: CancelOptions): Promise<void>;
    invalidateQueries<TTaggedQueryKey extends QueryKey = QueryKey>(filters?: InvalidateQueryFilters<TTaggedQueryKey>, options?: InvalidateOptions): Promise<void>;
    refetchQueries<TTaggedQueryKey extends QueryKey = QueryKey>(filters?: RefetchQueryFilters<TTaggedQueryKey>, options?: RefetchOptions): Promise<void>;
    fetchQuery<TQueryFnData, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey, TPageParam = never>(options: FetchQueryOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam>): Promise<TData>;
    prefetchQuery<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey>(options: FetchQueryOptions<TQueryFnData, TError, TData, TQueryKey>): Promise<void>;
    fetchInfiniteQuery<TQueryFnData, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey, TPageParam = unknown>(options: FetchInfiniteQueryOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam>): Promise<InfiniteData<TData, TPageParam>>;
    prefetchInfiniteQuery<TQueryFnData, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey, TPageParam = unknown>(options: FetchInfiniteQueryOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam>): Promise<void>;
    ensureInfiniteQueryData<TQueryFnData, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey, TPageParam = unknown>(options: EnsureInfiniteQueryDataOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam>): Promise<InfiniteData<TData, TPageParam>>;
    resumePausedMutations(): Promise<unknown>;
    getQueryCache(): QueryCache;
    getMutationCache(): MutationCache;
    getDefaultOptions(): DefaultOptions;
    setDefaultOptions(options: DefaultOptions): void;
    setQueryDefaults<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryData = TQueryFnData>(queryKey: QueryKey, options: Partial<OmitKeyof<QueryObserverOptions<TQueryFnData, TError, TData, TQueryData>, 'queryKey'>>): void;
    getQueryDefaults(queryKey: QueryKey): OmitKeyof<QueryObserverOptions<any, any, any, any, any>, 'queryKey'>;
    setMutationDefaults<TData = unknown, TError = DefaultError, TVariables = void, TOnMutateResult = unknown>(mutationKey: MutationKey, options: OmitKeyof<MutationObserverOptions<TData, TError, TVariables, TOnMutateResult>, 'mutationKey'>): void;
    getMutationDefaults(mutationKey: MutationKey): OmitKeyof<MutationObserverOptions<any, any, any, any>, 'mutationKey'>;
    defaultQueryOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryData = TQueryFnData, TQueryKey extends QueryKey = QueryKey, TPageParam = never>(options: QueryObserverOptions<TQueryFnData, TError, TData, TQueryData, TQueryKey, TPageParam> | DefaultedQueryObserverOptions<TQueryFnData, TError, TData, TQueryData, TQueryKey>): DefaultedQueryObserverOptions<TQueryFnData, TError, TData, TQueryData, TQueryKey>;
    defaultMutationOptions<T extends MutationOptions<any, any, any, any>>(options?: T): T;
    clear(): void;
}

interface RetryerConfig<TData = unknown, TError = DefaultError> {
    fn: () => TData | Promise<TData>;
    initialPromise?: Promise<TData>;
    onCancel?: (error: TError) => void;
    onFail?: (failureCount: number, error: TError) => void;
    onPause?: () => void;
    onContinue?: () => void;
    retry?: RetryValue<TError>;
    retryDelay?: RetryDelayValue<TError>;
    networkMode: NetworkMode | undefined;
    canRun: () => boolean;
}
interface Retryer<TData = unknown> {
    promise: Promise<TData>;
    cancel: (cancelOptions?: CancelOptions) => void;
    continue: () => Promise<unknown>;
    cancelRetry: () => void;
    continueRetry: () => void;
    canStart: () => boolean;
    start: () => Promise<TData>;
    status: () => 'pending' | 'resolved' | 'rejected';
}
type RetryValue<TError> = boolean | number | ShouldRetryFunction<TError>;
type ShouldRetryFunction<TError = DefaultError> = (failureCount: number, error: TError) => boolean;
type RetryDelayValue<TError> = number | RetryDelayFunction<TError>;
type RetryDelayFunction<TError = DefaultError> = (failureCount: number, error: TError) => number;
declare function canFetch(networkMode: NetworkMode | undefined): boolean;
declare class CancelledError extends Error {
    revert?: boolean;
    silent?: boolean;
    constructor(options?: CancelOptions);
}
/**
 * @deprecated Use instanceof `CancelledError` instead.
 */
declare function isCancelledError(value: any): value is CancelledError;
declare function createRetryer<TData = unknown, TError = DefaultError>(config: RetryerConfig<TData, TError>): Retryer<TData>;

type NonUndefinedGuard<T> = T extends undefined ? never : T;
type DistributiveOmit<TObject, TKey extends keyof TObject> = TObject extends any ? Omit<TObject, TKey> : never;
type OmitKeyof<TObject, TKey extends TStrictly extends 'safely' ? keyof TObject | (string & Record<never, never>) | (number & Record<never, never>) | (symbol & Record<never, never>) : keyof TObject, TStrictly extends 'strictly' | 'safely' = 'strictly'> = Omit<TObject, TKey>;
type Override<TTargetA, TTargetB> = {
    [AKey in keyof TTargetA]: AKey extends keyof TTargetB ? TTargetB[AKey] : TTargetA[AKey];
};
type NoInfer<T> = [T][T extends any ? 0 : never];
interface Register {
}
type DefaultError = Register extends {
    defaultError: infer TError;
} ? TError : Error;
type QueryKey = Register extends {
    queryKey: infer TQueryKey;
} ? TQueryKey extends ReadonlyArray<unknown> ? TQueryKey : TQueryKey extends Array<unknown> ? TQueryKey : ReadonlyArray<unknown> : ReadonlyArray<unknown>;
declare const dataTagSymbol: unique symbol;
type dataTagSymbol = typeof dataTagSymbol;
declare const dataTagErrorSymbol: unique symbol;
type dataTagErrorSymbol = typeof dataTagErrorSymbol;
declare const unsetMarker: unique symbol;
type UnsetMarker = typeof unsetMarker;
type AnyDataTag = {
    [dataTagSymbol]: any;
    [dataTagErrorSymbol]: any;
};
type DataTag<TType, TValue, TError = UnsetMarker> = TType extends AnyDataTag ? TType : TType & {
    [dataTagSymbol]: TValue;
    [dataTagErrorSymbol]: TError;
};
type InferDataFromTag<TQueryFnData, TTaggedQueryKey extends QueryKey> = TTaggedQueryKey extends DataTag<unknown, infer TaggedValue, unknown> ? TaggedValue : TQueryFnData;
type InferErrorFromTag<TError, TTaggedQueryKey extends QueryKey> = TTaggedQueryKey extends DataTag<unknown, unknown, infer TaggedError> ? TaggedError extends UnsetMarker ? TError : TaggedError : TError;
type QueryFunction<T = unknown, TQueryKey extends QueryKey = QueryKey, TPageParam = never> = (context: QueryFunctionContext<TQueryKey, TPageParam>) => T | Promise<T>;
type StaleTime = number | 'static';
type StaleTimeFunction<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey> = StaleTime | ((query: Query<TQueryFnData, TError, TData, TQueryKey>) => StaleTime);
type Enabled<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey> = boolean | ((query: Query<TQueryFnData, TError, TData, TQueryKey>) => boolean);
type QueryPersister<T = unknown, TQueryKey extends QueryKey = QueryKey, TPageParam = never> = [TPageParam] extends [never] ? (queryFn: QueryFunction<T, TQueryKey, never>, context: QueryFunctionContext<TQueryKey>, query: Query) => T | Promise<T> : (queryFn: QueryFunction<T, TQueryKey, TPageParam>, context: QueryFunctionContext<TQueryKey>, query: Query) => T | Promise<T>;
type QueryFunctionContext<TQueryKey extends QueryKey = QueryKey, TPageParam = never> = [TPageParam] extends [never] ? {
    client: QueryClient;
    queryKey: TQueryKey;
    signal: AbortSignal;
    meta: QueryMeta | undefined;
    pageParam?: unknown;
    /**
     * @deprecated
     * if you want access to the direction, you can add it to the pageParam
     */
    direction?: unknown;
} : {
    client: QueryClient;
    queryKey: TQueryKey;
    signal: AbortSignal;
    pageParam: TPageParam;
    /**
     * @deprecated
     * if you want access to the direction, you can add it to the pageParam
     */
    direction: FetchDirection;
    meta: QueryMeta | undefined;
};
type InitialDataFunction<T> = () => T | undefined;
type NonFunctionGuard<T> = T extends Function ? never : T;
type PlaceholderDataFunction<TQueryFnData = unknown, TError = DefaultError, TQueryData = TQueryFnData, TQueryKey extends QueryKey = QueryKey> = (previousData: TQueryData | undefined, previousQuery: Query<TQueryFnData, TError, TQueryData, TQueryKey> | undefined) => TQueryData | undefined;
type QueriesPlaceholderDataFunction<TQueryData> = (previousData: undefined, previousQuery: undefined) => TQueryData | undefined;
type QueryKeyHashFunction<TQueryKey extends QueryKey> = (queryKey: TQueryKey) => string;
type GetPreviousPageParamFunction<TPageParam, TQueryFnData = unknown> = (firstPage: TQueryFnData, allPages: Array<TQueryFnData>, firstPageParam: TPageParam, allPageParams: Array<TPageParam>) => TPageParam | undefined | null;
type GetNextPageParamFunction<TPageParam, TQueryFnData = unknown> = (lastPage: TQueryFnData, allPages: Array<TQueryFnData>, lastPageParam: TPageParam, allPageParams: Array<TPageParam>) => TPageParam | undefined | null;
interface InfiniteData<TData, TPageParam = unknown> {
    pages: Array<TData>;
    pageParams: Array<TPageParam>;
}
type QueryMeta = Register extends {
    queryMeta: infer TQueryMeta;
} ? TQueryMeta extends Record<string, unknown> ? TQueryMeta : Record<string, unknown> : Record<string, unknown>;
type NetworkMode = 'online' | 'always' | 'offlineFirst';
type NotifyOnChangeProps = Array<keyof InfiniteQueryObserverResult> | 'all' | undefined | (() => Array<keyof InfiniteQueryObserverResult> | 'all' | undefined);
interface QueryOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey, TPageParam = never> {
    /**
     * If `false`, failed queries will not retry by default.
     * If `true`, failed queries will retry infinitely., failureCount: num
     * If set to an integer number, e.g. 3, failed queries will retry until the failed query count meets that number.
     * If set to a function `(failureCount, error) => boolean` failed queries will retry until the function returns false.
     */
    retry?: RetryValue<TError>;
    retryDelay?: RetryDelayValue<TError>;
    networkMode?: NetworkMode;
    /**
     * The time in milliseconds that unused/inactive cache data remains in memory.
     * When a query's cache becomes unused or inactive, that cache data will be garbage collected after this duration.
     * When different garbage collection times are specified, the longest one will be used.
     * Setting it to `Infinity` will disable garbage collection.
     */
    gcTime?: number;
    queryFn?: QueryFunction<TQueryFnData, TQueryKey, TPageParam> | SkipToken;
    persister?: QueryPersister<NoInfer<TQueryFnData>, NoInfer<TQueryKey>, NoInfer<TPageParam>>;
    queryHash?: string;
    queryKey?: TQueryKey;
    queryKeyHashFn?: QueryKeyHashFunction<TQueryKey>;
    initialData?: TData | InitialDataFunction<TData>;
    initialDataUpdatedAt?: number | (() => number | undefined);
    behavior?: QueryBehavior<TQueryFnData, TError, TData, TQueryKey>;
    /**
     * Set this to `false` to disable structural sharing between query results.
     * Set this to a function which accepts the old and new data and returns resolved data of the same type to implement custom structural sharing logic.
     * Defaults to `true`.
     */
    structuralSharing?: boolean | ((oldData: unknown | undefined, newData: unknown) => unknown);
    _defaulted?: boolean;
    /**
     * Additional payload to be stored on each query.
     * Use this property to pass information that can be used in other places.
     */
    meta?: QueryMeta;
    /**
     * Maximum number of pages to store in the data of an infinite query.
     */
    maxPages?: number;
}
interface InitialPageParam<TPageParam = unknown> {
    initialPageParam: TPageParam;
}
interface InfiniteQueryPageParamsOptions<TQueryFnData = unknown, TPageParam = unknown> extends InitialPageParam<TPageParam> {
    /**
     * This function can be set to automatically get the previous cursor for infinite queries.
     * The result will also be used to determine the value of `hasPreviousPage`.
     */
    getPreviousPageParam?: GetPreviousPageParamFunction<TPageParam, TQueryFnData>;
    /**
     * This function can be set to automatically get the next cursor for infinite queries.
     * The result will also be used to determine the value of `hasNextPage`.
     */
    getNextPageParam: GetNextPageParamFunction<TPageParam, TQueryFnData>;
}
type ThrowOnError<TQueryFnData, TError, TQueryData, TQueryKey extends QueryKey> = boolean | ((error: TError, query: Query<TQueryFnData, TError, TQueryData, TQueryKey>) => boolean);
interface QueryObserverOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryData = TQueryFnData, TQueryKey extends QueryKey = QueryKey, TPageParam = never> extends WithRequired<QueryOptions<TQueryFnData, TError, TQueryData, TQueryKey, TPageParam>, 'queryKey'> {
    /**
     * Set this to `false` or a function that returns `false` to disable automatic refetching when the query mounts or changes query keys.
     * To refetch the query, use the `refetch` method returned from the `useQuery` instance.
     * Accepts a boolean or function that returns a boolean.
     * Defaults to `true`.
     */
    enabled?: Enabled<TQueryFnData, TError, TQueryData, TQueryKey>;
    /**
     * The time in milliseconds after data is considered stale.
     * If set to `Infinity`, the data will never be considered stale.
     * If set to a function, the function will be executed with the query to compute a `staleTime`.
     * Defaults to `0`.
     */
    staleTime?: StaleTimeFunction<TQueryFnData, TError, TQueryData, TQueryKey>;
    /**
     * If set to a number, the query will continuously refetch at this frequency in milliseconds.
     * If set to a function, the function will be executed with the latest data and query to compute a frequency
     * Defaults to `false`.
     */
    refetchInterval?: number | false | ((query: Query<TQueryFnData, TError, TQueryData, TQueryKey>) => number | false | undefined);
    /**
     * If set to `true`, the query will continue to refetch while their tab/window is in the background.
     * Defaults to `false`.
     */
    refetchIntervalInBackground?: boolean;
    /**
     * If set to `true`, the query will refetch on window focus if the data is stale.
     * If set to `false`, the query will not refetch on window focus.
     * If set to `'always'`, the query will always refetch on window focus.
     * If set to a function, the function will be executed with the latest data and query to compute the value.
     * Defaults to `true`.
     */
    refetchOnWindowFocus?: boolean | 'always' | ((query: Query<TQueryFnData, TError, TQueryData, TQueryKey>) => boolean | 'always');
    /**
     * If set to `true`, the query will refetch on reconnect if the data is stale.
     * If set to `false`, the query will not refetch on reconnect.
     * If set to `'always'`, the query will always refetch on reconnect.
     * If set to a function, the function will be executed with the latest data and query to compute the value.
     * Defaults to the value of `networkOnline` (`true`)
     */
    refetchOnReconnect?: boolean | 'always' | ((query: Query<TQueryFnData, TError, TQueryData, TQueryKey>) => boolean | 'always');
    /**
     * If set to `true`, the query will refetch on mount if the data is stale.
     * If set to `false`, will disable additional instances of a query to trigger background refetch.
     * If set to `'always'`, the query will always refetch on mount.
     * If set to a function, the function will be executed with the latest data and query to compute the value
     * Defaults to `true`.
     */
    refetchOnMount?: boolean | 'always' | ((query: Query<TQueryFnData, TError, TQueryData, TQueryKey>) => boolean | 'always');
    /**
     * If set to `false`, the query will not be retried on mount if it contains an error.
     * Defaults to `true`.
     */
    retryOnMount?: boolean;
    /**
     * If set, the component will only re-render if any of the listed properties change.
     * When set to `['data', 'error']`, the component will only re-render when the `data` or `error` properties change.
     * When set to `'all'`, the component will re-render whenever a query is updated.
     * When set to a function, the function will be executed to compute the list of properties.
     * By default, access to properties will be tracked, and the component will only re-render when one of the tracked properties change.
     */
    notifyOnChangeProps?: NotifyOnChangeProps;
    /**
     * Whether errors should be thrown instead of setting the `error` property.
     * If set to `true` or `suspense` is `true`, all errors will be thrown to the error boundary.
     * If set to `false` and `suspense` is `false`, errors are returned as state.
     * If set to a function, it will be passed the error and the query, and it should return a boolean indicating whether to show the error in an error boundary (`true`) or return the error as state (`false`).
     * Defaults to `false`.
     */
    throwOnError?: ThrowOnError<TQueryFnData, TError, TQueryData, TQueryKey>;
    /**
     * This option can be used to transform or select a part of the data returned by the query function.
     */
    select?: (data: TQueryData) => TData;
    /**
     * If set to `true`, the query will suspend when `status === 'pending'`
     * and throw errors when `status === 'error'`.
     * Defaults to `false`.
     */
    suspense?: boolean;
    /**
     * If set, this value will be used as the placeholder data for this particular query observer while the query is still in the `loading` data and no initialData has been provided.
     */
    placeholderData?: NonFunctionGuard<TQueryData> | PlaceholderDataFunction<NonFunctionGuard<TQueryData>, TError, NonFunctionGuard<TQueryData>, TQueryKey>;
    _optimisticResults?: 'optimistic' | 'isRestoring';
    /**
     * Enable prefetching during rendering
     */
    experimental_prefetchInRender?: boolean;
}
type WithRequired<TTarget, TKey extends keyof TTarget> = TTarget & {
    [_ in TKey]: {};
};
type DefaultedQueryObserverOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryData = TQueryFnData, TQueryKey extends QueryKey = QueryKey> = WithRequired<QueryObserverOptions<TQueryFnData, TError, TData, TQueryData, TQueryKey>, 'throwOnError' | 'refetchOnReconnect' | 'queryHash'>;
interface InfiniteQueryObserverOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey, TPageParam = unknown> extends QueryObserverOptions<TQueryFnData, TError, TData, InfiniteData<TQueryFnData, TPageParam>, TQueryKey, TPageParam>, InfiniteQueryPageParamsOptions<TQueryFnData, TPageParam> {
}
type DefaultedInfiniteQueryObserverOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey, TPageParam = unknown> = WithRequired<InfiniteQueryObserverOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam>, 'throwOnError' | 'refetchOnReconnect' | 'queryHash'>;
interface FetchQueryOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey, TPageParam = never> extends WithRequired<QueryOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam>, 'queryKey'> {
    initialPageParam?: never;
    /**
     * The time in milliseconds after data is considered stale.
     * If the data is fresh it will be returned from the cache.
     */
    staleTime?: StaleTimeFunction<TQueryFnData, TError, TData, TQueryKey>;
}
interface EnsureQueryDataOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey, TPageParam = never> extends FetchQueryOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam> {
    revalidateIfStale?: boolean;
}
type EnsureInfiniteQueryDataOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey, TPageParam = unknown> = FetchInfiniteQueryOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam> & {
    revalidateIfStale?: boolean;
};
type FetchInfiniteQueryPages<TQueryFnData = unknown, TPageParam = unknown> = {
    pages?: never;
} | {
    pages: number;
    getNextPageParam: GetNextPageParamFunction<TPageParam, TQueryFnData>;
};
type FetchInfiniteQueryOptions<TQueryFnData = unknown, TError = DefaultError, TData = TQueryFnData, TQueryKey extends QueryKey = QueryKey, TPageParam = unknown> = Omit<FetchQueryOptions<TQueryFnData, TError, InfiniteData<TData, TPageParam>, TQueryKey, TPageParam>, 'initialPageParam'> & InitialPageParam<TPageParam> & FetchInfiniteQueryPages<TQueryFnData, TPageParam>;
interface ResultOptions {
    throwOnError?: boolean;
}
interface RefetchOptions extends ResultOptions {
    /**
     * If set to `true`, a currently running request will be cancelled before a new request is made
     *
     * If set to `false`, no refetch will be made if there is already a request running.
     *
     * Defaults to `true`.
     */
    cancelRefetch?: boolean;
}
interface InvalidateQueryFilters<TQueryKey extends QueryKey = QueryKey> extends QueryFilters<TQueryKey> {
    refetchType?: QueryTypeFilter | 'none';
}
interface RefetchQueryFilters<TQueryKey extends QueryKey = QueryKey> extends QueryFilters<TQueryKey> {
}
interface InvalidateOptions extends RefetchOptions {
}
interface ResetOptions extends RefetchOptions {
}
interface FetchNextPageOptions extends ResultOptions {
    /**
     * If set to `true`, calling `fetchNextPage` repeatedly will invoke `queryFn` every time,
     * whether the previous invocation has resolved or not. Also, the result from previous invocations will be ignored.
     *
     * If set to `false`, calling `fetchNextPage` repeatedly won't have any effect until the first invocation has resolved.
     *
     * Defaults to `true`.
     */
    cancelRefetch?: boolean;
}
interface FetchPreviousPageOptions extends ResultOptions {
    /**
     * If set to `true`, calling `fetchPreviousPage` repeatedly will invoke `queryFn` every time,
     * whether the previous invocation has resolved or not. Also, the result from previous invocations will be ignored.
     *
     * If set to `false`, calling `fetchPreviousPage` repeatedly won't have any effect until the first invocation has resolved.
     *
     * Defaults to `true`.
     */
    cancelRefetch?: boolean;
}
type QueryStatus = 'pending' | 'error' | 'success';
type FetchStatus = 'fetching' | 'paused' | 'idle';
interface QueryObserverBaseResult<TData = unknown, TError = DefaultError> {
    /**
     * The last successfully resolved data for the query.
     */
    data: TData | undefined;
    /**
     * The timestamp for when the query most recently returned the `status` as `"success"`.
     */
    dataUpdatedAt: number;
    /**
     * The error object for the query, if an error was thrown.
     * - Defaults to `null`.
     */
    error: TError | null;
    /**
     * The timestamp for when the query most recently returned the `status` as `"error"`.
     */
    errorUpdatedAt: number;
    /**
     * The failure count for the query.
     * - Incremented every time the query fails.
     * - Reset to `0` when the query succeeds.
     */
    failureCount: number;
    /**
     * The failure reason for the query retry.
     * - Reset to `null` when the query succeeds.
     */
    failureReason: TError | null;
    /**
     * The sum of all errors.
     */
    errorUpdateCount: number;
    /**
     * A derived boolean from the `status` variable, provided for convenience.
     * - `true` if the query attempt resulted in an error.
     */
    isError: boolean;
    /**
     * Will be `true` if the query has been fetched.
     */
    isFetched: boolean;
    /**
     * Will be `true` if the query has been fetched after the component mounted.
     * - This property can be used to not show any previously cached data.
     */
    isFetchedAfterMount: boolean;
    /**
     * A derived boolean from the `fetchStatus` variable, provided for convenience.
     * - `true` whenever the `queryFn` is executing, which includes initial `pending` as well as background refetch.
     */
    isFetching: boolean;
    /**
     * Is `true` whenever the first fetch for a query is in-flight.
     * - Is the same as `isFetching && isPending`.
     */
    isLoading: boolean;
    /**
     * Will be `pending` if there's no cached data and no query attempt was finished yet.
     */
    isPending: boolean;
    /**
     * Will be `true` if the query failed while fetching for the first time.
     */
    isLoadingError: boolean;
    /**
     * @deprecated `isInitialLoading` is being deprecated in favor of `isLoading`
     * and will be removed in the next major version.
     */
    isInitialLoading: boolean;
    /**
     * A derived boolean from the `fetchStatus` variable, provided for convenience.
     * - The query wanted to fetch, but has been `paused`.
     */
    isPaused: boolean;
    /**
     * Will be `true` if the data shown is the placeholder data.
     */
    isPlaceholderData: boolean;
    /**
     * Will be `true` if the query failed while refetching.
     */
    isRefetchError: boolean;
    /**
     * Is `true` whenever a background refetch is in-flight, which _does not_ include initial `pending`.
     * - Is the same as `isFetching && !isPending`.
     */
    isRefetching: boolean;
    /**
     * Will be `true` if the data in the cache is invalidated or if the data is older than the given `staleTime`.
     */
    isStale: boolean;
    /**
     * A derived boolean from the `status` variable, provided for convenience.
     * - `true` if the query has received a response with no errors and is ready to display its data.
     */
    isSuccess: boolean;
    /**
     * `true` if this observer is enabled, `false` otherwise.
     */
    isEnabled: boolean;
    /**
     * A function to manually refetch the query.
     */
    refetch: (options?: RefetchOptions) => Promise<QueryObserverResult<TData, TError>>;
    /**
     * The status of the query.
     * - Will be:
     *   - `pending` if there's no cached data and no query attempt was finished yet.
     *   - `error` if the query attempt resulted in an error.
     *   - `success` if the query has received a response with no errors and is ready to display its data.
     */
    status: QueryStatus;
    /**
     * The fetch status of the query.
     * - `fetching`: Is `true` whenever the queryFn is executing, which includes initial `pending` as well as background refetch.
     * - `paused`: The query wanted to fetch, but has been `paused`.
     * - `idle`: The query is not fetching.
     * - See [Network Mode](https://tanstack.com/query/latest/docs/framework/react/guides/network-mode) for more information.
     */
    fetchStatus: FetchStatus;
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
    promise: Promise<TData>;
}
interface QueryObserverPendingResult<TData = unknown, TError = DefaultError> extends QueryObserverBaseResult<TData, TError> {
    data: undefined;
    error: null;
    isError: false;
    isPending: true;
    isLoadingError: false;
    isRefetchError: false;
    isSuccess: false;
    isPlaceholderData: false;
    status: 'pending';
}
interface QueryObserverLoadingResult<TData = unknown, TError = DefaultError> extends QueryObserverBaseResult<TData, TError> {
    data: undefined;
    error: null;
    isError: false;
    isPending: true;
    isLoading: true;
    isLoadingError: false;
    isRefetchError: false;
    isSuccess: false;
    isPlaceholderData: false;
    status: 'pending';
}
interface QueryObserverLoadingErrorResult<TData = unknown, TError = DefaultError> extends QueryObserverBaseResult<TData, TError> {
    data: undefined;
    error: TError;
    isError: true;
    isPending: false;
    isLoading: false;
    isLoadingError: true;
    isRefetchError: false;
    isSuccess: false;
    isPlaceholderData: false;
    status: 'error';
}
interface QueryObserverRefetchErrorResult<TData = unknown, TError = DefaultError> extends QueryObserverBaseResult<TData, TError> {
    data: TData;
    error: TError;
    isError: true;
    isPending: false;
    isLoading: false;
    isLoadingError: false;
    isRefetchError: true;
    isSuccess: false;
    isPlaceholderData: false;
    status: 'error';
}
interface QueryObserverSuccessResult<TData = unknown, TError = DefaultError> extends QueryObserverBaseResult<TData, TError> {
    data: TData;
    error: null;
    isError: false;
    isPending: false;
    isLoading: false;
    isLoadingError: false;
    isRefetchError: false;
    isSuccess: true;
    isPlaceholderData: false;
    status: 'success';
}
interface QueryObserverPlaceholderResult<TData = unknown, TError = DefaultError> extends QueryObserverBaseResult<TData, TError> {
    data: TData;
    isError: false;
    error: null;
    isPending: false;
    isLoading: false;
    isLoadingError: false;
    isRefetchError: false;
    isSuccess: true;
    isPlaceholderData: true;
    status: 'success';
}
type DefinedQueryObserverResult<TData = unknown, TError = DefaultError> = QueryObserverRefetchErrorResult<TData, TError> | QueryObserverSuccessResult<TData, TError>;
type QueryObserverResult<TData = unknown, TError = DefaultError> = DefinedQueryObserverResult<TData, TError> | QueryObserverLoadingErrorResult<TData, TError> | QueryObserverLoadingResult<TData, TError> | QueryObserverPendingResult<TData, TError> | QueryObserverPlaceholderResult<TData, TError>;
interface InfiniteQueryObserverBaseResult<TData = unknown, TError = DefaultError> extends QueryObserverBaseResult<TData, TError> {
    /**
     * This function allows you to fetch the next "page" of results.
     */
    fetchNextPage: (options?: FetchNextPageOptions) => Promise<InfiniteQueryObserverResult<TData, TError>>;
    /**
     * This function allows you to fetch the previous "page" of results.
     */
    fetchPreviousPage: (options?: FetchPreviousPageOptions) => Promise<InfiniteQueryObserverResult<TData, TError>>;
    /**
     * Will be `true` if there is a next page to be fetched (known via the `getNextPageParam` option).
     */
    hasNextPage: boolean;
    /**
     * Will be `true` if there is a previous page to be fetched (known via the `getPreviousPageParam` option).
     */
    hasPreviousPage: boolean;
    /**
     * Will be `true` if the query failed while fetching the next page.
     */
    isFetchNextPageError: boolean;
    /**
     * Will be `true` while fetching the next page with `fetchNextPage`.
     */
    isFetchingNextPage: boolean;
    /**
     * Will be `true` if the query failed while fetching the previous page.
     */
    isFetchPreviousPageError: boolean;
    /**
     * Will be `true` while fetching the previous page with `fetchPreviousPage`.
     */
    isFetchingPreviousPage: boolean;
}
interface InfiniteQueryObserverPendingResult<TData = unknown, TError = DefaultError> extends InfiniteQueryObserverBaseResult<TData, TError> {
    data: undefined;
    error: null;
    isError: false;
    isPending: true;
    isLoadingError: false;
    isRefetchError: false;
    isFetchNextPageError: false;
    isFetchPreviousPageError: false;
    isSuccess: false;
    isPlaceholderData: false;
    status: 'pending';
}
interface InfiniteQueryObserverLoadingResult<TData = unknown, TError = DefaultError> extends InfiniteQueryObserverBaseResult<TData, TError> {
    data: undefined;
    error: null;
    isError: false;
    isPending: true;
    isLoading: true;
    isLoadingError: false;
    isRefetchError: false;
    isFetchNextPageError: false;
    isFetchPreviousPageError: false;
    isSuccess: false;
    isPlaceholderData: false;
    status: 'pending';
}
interface InfiniteQueryObserverLoadingErrorResult<TData = unknown, TError = DefaultError> extends InfiniteQueryObserverBaseResult<TData, TError> {
    data: undefined;
    error: TError;
    isError: true;
    isPending: false;
    isLoading: false;
    isLoadingError: true;
    isRefetchError: false;
    isFetchNextPageError: false;
    isFetchPreviousPageError: false;
    isSuccess: false;
    isPlaceholderData: false;
    status: 'error';
}
interface InfiniteQueryObserverRefetchErrorResult<TData = unknown, TError = DefaultError> extends InfiniteQueryObserverBaseResult<TData, TError> {
    data: TData;
    error: TError;
    isError: true;
    isPending: false;
    isLoading: false;
    isLoadingError: false;
    isRefetchError: true;
    isSuccess: false;
    isPlaceholderData: false;
    status: 'error';
}
interface InfiniteQueryObserverSuccessResult<TData = unknown, TError = DefaultError> extends InfiniteQueryObserverBaseResult<TData, TError> {
    data: TData;
    error: null;
    isError: false;
    isPending: false;
    isLoading: false;
    isLoadingError: false;
    isRefetchError: false;
    isFetchNextPageError: false;
    isFetchPreviousPageError: false;
    isSuccess: true;
    isPlaceholderData: false;
    status: 'success';
}
interface InfiniteQueryObserverPlaceholderResult<TData = unknown, TError = DefaultError> extends InfiniteQueryObserverBaseResult<TData, TError> {
    data: TData;
    isError: false;
    error: null;
    isPending: false;
    isLoading: false;
    isLoadingError: false;
    isRefetchError: false;
    isSuccess: true;
    isPlaceholderData: true;
    isFetchNextPageError: false;
    isFetchPreviousPageError: false;
    status: 'success';
}
type DefinedInfiniteQueryObserverResult<TData = unknown, TError = DefaultError> = InfiniteQueryObserverRefetchErrorResult<TData, TError> | InfiniteQueryObserverSuccessResult<TData, TError>;
type InfiniteQueryObserverResult<TData = unknown, TError = DefaultError> = DefinedInfiniteQueryObserverResult<TData, TError> | InfiniteQueryObserverLoadingErrorResult<TData, TError> | InfiniteQueryObserverLoadingResult<TData, TError> | InfiniteQueryObserverPendingResult<TData, TError> | InfiniteQueryObserverPlaceholderResult<TData, TError>;
type MutationKey = Register extends {
    mutationKey: infer TMutationKey;
} ? TMutationKey extends Array<unknown> ? TMutationKey : TMutationKey extends Array<unknown> ? TMutationKey : ReadonlyArray<unknown> : ReadonlyArray<unknown>;
type MutationStatus = 'idle' | 'pending' | 'success' | 'error';
type MutationScope = {
    id: string;
};
type MutationMeta = Register extends {
    mutationMeta: infer TMutationMeta;
} ? TMutationMeta extends Record<string, unknown> ? TMutationMeta : Record<string, unknown> : Record<string, unknown>;
type MutationFunctionContext = {
    client: QueryClient;
    meta: MutationMeta | undefined;
    mutationKey?: MutationKey;
};
type MutationFunction<TData = unknown, TVariables = unknown> = (variables: TVariables, context: MutationFunctionContext) => Promise<TData>;
interface MutationOptions<TData = unknown, TError = DefaultError, TVariables = void, TOnMutateResult = unknown> {
    mutationFn?: MutationFunction<TData, TVariables>;
    mutationKey?: MutationKey;
    onMutate?: (variables: TVariables, context: MutationFunctionContext) => Promise<TOnMutateResult> | TOnMutateResult;
    onSuccess?: (data: TData, variables: TVariables, onMutateResult: TOnMutateResult, context: MutationFunctionContext) => Promise<unknown> | unknown;
    onError?: (error: TError, variables: TVariables, onMutateResult: TOnMutateResult | undefined, context: MutationFunctionContext) => Promise<unknown> | unknown;
    onSettled?: (data: TData | undefined, error: TError | null, variables: TVariables, onMutateResult: TOnMutateResult | undefined, context: MutationFunctionContext) => Promise<unknown> | unknown;
    retry?: RetryValue<TError>;
    retryDelay?: RetryDelayValue<TError>;
    networkMode?: NetworkMode;
    gcTime?: number;
    _defaulted?: boolean;
    meta?: MutationMeta;
    scope?: MutationScope;
}
interface MutationObserverOptions<TData = unknown, TError = DefaultError, TVariables = void, TOnMutateResult = unknown> extends MutationOptions<TData, TError, TVariables, TOnMutateResult> {
    throwOnError?: boolean | ((error: TError) => boolean);
}
interface MutateOptions<TData = unknown, TError = DefaultError, TVariables = void, TOnMutateResult = unknown> {
    onSuccess?: (data: TData, variables: TVariables, onMutateResult: TOnMutateResult | undefined, context: MutationFunctionContext) => void;
    onError?: (error: TError, variables: TVariables, onMutateResult: TOnMutateResult | undefined, context: MutationFunctionContext) => void;
    onSettled?: (data: TData | undefined, error: TError | null, variables: TVariables, onMutateResult: TOnMutateResult | undefined, context: MutationFunctionContext) => void;
}
type MutateFunction<TData = unknown, TError = DefaultError, TVariables = void, TOnMutateResult = unknown> = (variables: TVariables, options?: MutateOptions<TData, TError, TVariables, TOnMutateResult>) => Promise<TData>;
interface MutationObserverBaseResult<TData = unknown, TError = DefaultError, TVariables = void, TOnMutateResult = unknown> extends MutationState<TData, TError, TVariables, TOnMutateResult> {
    /**
     * The last successfully resolved data for the mutation.
     */
    data: TData | undefined;
    /**
     * The variables object passed to the `mutationFn`.
     */
    variables: TVariables | undefined;
    /**
     * The error object for the mutation, if an error was encountered.
     * - Defaults to `null`.
     */
    error: TError | null;
    /**
     * A boolean variable derived from `status`.
     * - `true` if the last mutation attempt resulted in an error.
     */
    isError: boolean;
    /**
     * A boolean variable derived from `status`.
     * - `true` if the mutation is in its initial state prior to executing.
     */
    isIdle: boolean;
    /**
     * A boolean variable derived from `status`.
     * - `true` if the mutation is currently executing.
     */
    isPending: boolean;
    /**
     * A boolean variable derived from `status`.
     * - `true` if the last mutation attempt was successful.
     */
    isSuccess: boolean;
    /**
     * The status of the mutation.
     * - Will be:
     *   - `idle` initial status prior to the mutation function executing.
     *   - `pending` if the mutation is currently executing.
     *   - `error` if the last mutation attempt resulted in an error.
     *   - `success` if the last mutation attempt was successful.
     */
    status: MutationStatus;
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
    mutate: MutateFunction<TData, TError, TVariables, TOnMutateResult>;
    /**
     * A function to clean the mutation internal state (i.e., it resets the mutation to its initial state).
     */
    reset: () => void;
}
interface MutationObserverIdleResult<TData = unknown, TError = DefaultError, TVariables = void, TOnMutateResult = unknown> extends MutationObserverBaseResult<TData, TError, TVariables, TOnMutateResult> {
    data: undefined;
    variables: undefined;
    error: null;
    isError: false;
    isIdle: true;
    isPending: false;
    isSuccess: false;
    status: 'idle';
}
interface MutationObserverLoadingResult<TData = unknown, TError = DefaultError, TVariables = void, TOnMutateResult = unknown> extends MutationObserverBaseResult<TData, TError, TVariables, TOnMutateResult> {
    data: undefined;
    variables: TVariables;
    error: null;
    isError: false;
    isIdle: false;
    isPending: true;
    isSuccess: false;
    status: 'pending';
}
interface MutationObserverErrorResult<TData = unknown, TError = DefaultError, TVariables = void, TOnMutateResult = unknown> extends MutationObserverBaseResult<TData, TError, TVariables, TOnMutateResult> {
    data: undefined;
    error: TError;
    variables: TVariables;
    isError: true;
    isIdle: false;
    isPending: false;
    isSuccess: false;
    status: 'error';
}
interface MutationObserverSuccessResult<TData = unknown, TError = DefaultError, TVariables = void, TOnMutateResult = unknown> extends MutationObserverBaseResult<TData, TError, TVariables, TOnMutateResult> {
    data: TData;
    error: null;
    variables: TVariables;
    isError: false;
    isIdle: false;
    isPending: false;
    isSuccess: true;
    status: 'success';
}
type MutationObserverResult<TData = unknown, TError = DefaultError, TVariables = void, TOnMutateResult = unknown> = MutationObserverIdleResult<TData, TError, TVariables, TOnMutateResult> | MutationObserverLoadingResult<TData, TError, TVariables, TOnMutateResult> | MutationObserverErrorResult<TData, TError, TVariables, TOnMutateResult> | MutationObserverSuccessResult<TData, TError, TVariables, TOnMutateResult>;
interface QueryClientConfig {
    queryCache?: QueryCache;
    mutationCache?: MutationCache;
    defaultOptions?: DefaultOptions;
}
interface DefaultOptions<TError = DefaultError> {
    queries?: OmitKeyof<QueryObserverOptions<unknown, TError>, 'suspense' | 'queryKey'>;
    mutations?: MutationObserverOptions<unknown, TError, unknown, unknown>;
    hydrate?: HydrateOptions['defaultOptions'];
    dehydrate?: DehydrateOptions;
}
interface CancelOptions {
    revert?: boolean;
    silent?: boolean;
}
interface SetDataOptions {
    updatedAt?: number;
}
type NotifyEventType = 'added' | 'removed' | 'updated' | 'observerAdded' | 'observerRemoved' | 'observerResultsUpdated' | 'observerOptionsUpdated';
interface NotifyEvent {
    type: NotifyEventType;
}

type TransformerFn = (data: any) => any;
interface DehydrateOptions {
    serializeData?: TransformerFn;
    shouldDehydrateMutation?: (mutation: Mutation) => boolean;
    shouldDehydrateQuery?: (query: Query) => boolean;
    shouldRedactErrors?: (error: unknown) => boolean;
}
interface HydrateOptions {
    defaultOptions?: {
        deserializeData?: TransformerFn;
        queries?: QueryOptions;
        mutations?: MutationOptions<unknown, DefaultError, unknown, unknown>;
    };
}
interface DehydratedMutation {
    mutationKey?: MutationKey;
    state: MutationState;
    meta?: MutationMeta;
    scope?: MutationScope;
}
interface DehydratedQuery {
    queryHash: string;
    queryKey: QueryKey;
    state: QueryState;
    promise?: Promise<unknown>;
    meta?: QueryMeta;
    dehydratedAt?: number;
}
interface DehydratedState {
    mutations: Array<DehydratedMutation>;
    queries: Array<DehydratedQuery>;
}
declare function defaultShouldDehydrateMutation(mutation: Mutation): boolean;
declare function defaultShouldDehydrateQuery(query: Query): boolean;
declare function dehydrate(client: QueryClient, options?: DehydrateOptions): DehydratedState;
declare function hydrate(client: QueryClient, dehydratedState: unknown, options?: HydrateOptions): void;

export { type Enabled as $, type QueryState as A, type DistributiveOmit as B, CancelledError as C, type DehydratedState as D, type Override as E, type NoInfer as F, type DefaultError as G, type HydrateOptions as H, type QueryKey as I, dataTagSymbol as J, dataTagErrorSymbol as K, unsetMarker as L, MutationCache as M, type NonUndefinedGuard as N, type OmitKeyof as O, type UnsetMarker as P, QueryCache as Q, type Register as R, type SkipToken as S, type AnyDataTag as T, type Updater as U, type DataTag as V, type InferDataFromTag as W, type InferErrorFromTag as X, type QueryFunction as Y, type StaleTime as Z, type StaleTimeFunction as _, defaultShouldDehydrateQuery as a, type MutationObserverBaseResult as a$, type QueryPersister as a0, type QueryFunctionContext as a1, type InitialDataFunction as a2, type PlaceholderDataFunction as a3, type QueriesPlaceholderDataFunction as a4, type QueryKeyHashFunction as a5, type GetPreviousPageParamFunction as a6, type GetNextPageParamFunction as a7, type InfiniteData as a8, type QueryMeta as a9, type QueryObserverPendingResult as aA, type QueryObserverLoadingResult as aB, type QueryObserverLoadingErrorResult as aC, type QueryObserverRefetchErrorResult as aD, type QueryObserverSuccessResult as aE, type QueryObserverPlaceholderResult as aF, type DefinedQueryObserverResult as aG, type QueryObserverResult as aH, type InfiniteQueryObserverBaseResult as aI, type InfiniteQueryObserverPendingResult as aJ, type InfiniteQueryObserverLoadingResult as aK, type InfiniteQueryObserverLoadingErrorResult as aL, type InfiniteQueryObserverRefetchErrorResult as aM, type InfiniteQueryObserverSuccessResult as aN, type InfiniteQueryObserverPlaceholderResult as aO, type DefinedInfiniteQueryObserverResult as aP, type InfiniteQueryObserverResult as aQ, type MutationKey as aR, type MutationStatus as aS, type MutationScope as aT, type MutationMeta as aU, type MutationFunctionContext as aV, type MutationFunction as aW, type MutationOptions as aX, type MutationObserverOptions as aY, type MutateOptions as aZ, type MutateFunction as a_, type NetworkMode as aa, type NotifyOnChangeProps as ab, type QueryOptions as ac, type InitialPageParam as ad, type InfiniteQueryPageParamsOptions as ae, type ThrowOnError as af, type QueryObserverOptions as ag, type WithRequired as ah, type DefaultedQueryObserverOptions as ai, type InfiniteQueryObserverOptions as aj, type DefaultedInfiniteQueryObserverOptions as ak, type FetchQueryOptions as al, type EnsureQueryDataOptions as am, type EnsureInfiniteQueryDataOptions as an, type FetchInfiniteQueryOptions as ao, type ResultOptions as ap, type RefetchOptions as aq, type InvalidateQueryFilters as ar, type RefetchQueryFilters as as, type InvalidateOptions as at, type ResetOptions as au, type FetchNextPageOptions as av, type FetchPreviousPageOptions as aw, type QueryStatus as ax, type FetchStatus as ay, type QueryObserverBaseResult as az, dehydrate as b, type MutationObserverIdleResult as b0, type MutationObserverLoadingResult as b1, type MutationObserverErrorResult as b2, type MutationObserverSuccessResult as b3, type MutationObserverResult as b4, type QueryClientConfig as b5, type DefaultOptions as b6, type CancelOptions as b7, type SetDataOptions as b8, type NotifyEventType as b9, type QueryStore as bA, type Retryer as bB, type RetryValue as bC, type RetryDelayValue as bD, canFetch as bE, createRetryer as bF, type NotifyEvent as ba, type QueryBehavior as bb, type FetchContext as bc, type FetchDirection as bd, type FetchMeta as be, type FetchOptions as bf, type Action$1 as bg, type SetStateOptions as bh, fetchState as bi, type Action as bj, getDefaultState as bk, type QueryTypeFilter as bl, functionalUpdate as bm, isValidTimeout as bn, timeUntilStale as bo, resolveStaleTime as bp, resolveEnabled as bq, hashQueryKeyByOptions as br, shallowEqualObjects as bs, isPlainArray as bt, isPlainObject as bu, sleep as bv, replaceData as bw, addToEnd as bx, addToStart as by, ensureQueryFn as bz, type MutationCacheNotifyEvent as c, defaultShouldDehydrateMutation as d, MutationObserver as e, type QueryCacheNotifyEvent as f, QueryClient as g, hydrate as h, QueryObserver as i, isCancelledError as j, hashKey as k, isServer as l, keepPreviousData as m, matchMutation as n, matchQuery as o, noop as p, partialMatchKey as q, replaceEqualDeep as r, shouldThrowError as s, skipToken as t, type MutationFilters as u, type QueryFilters as v, type DehydrateOptions as w, Mutation as x, type MutationState as y, Query as z };
