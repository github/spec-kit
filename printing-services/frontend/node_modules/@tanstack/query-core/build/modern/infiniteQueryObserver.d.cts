import { G as DefaultError, a8 as InfiniteData, I as QueryKey, i as QueryObserver, aQ as InfiniteQueryObserverResult, g as QueryClient, aj as InfiniteQueryObserverOptions, ak as DefaultedInfiniteQueryObserverOptions, av as FetchNextPageOptions, aw as FetchPreviousPageOptions, z as Query } from './hydration-CGqN5JZ-.cjs';
import { Subscribable } from './subscribable.cjs';
import './removable.cjs';

type InfiniteQueryObserverListener<TData, TError> = (result: InfiniteQueryObserverResult<TData, TError>) => void;
declare class InfiniteQueryObserver<TQueryFnData = unknown, TError = DefaultError, TData = InfiniteData<TQueryFnData>, TQueryKey extends QueryKey = QueryKey, TPageParam = unknown> extends QueryObserver<TQueryFnData, TError, TData, InfiniteData<TQueryFnData, TPageParam>, TQueryKey> {
    subscribe: Subscribable<InfiniteQueryObserverListener<TData, TError>>['subscribe'];
    getCurrentResult: ReplaceReturnType<QueryObserver<TQueryFnData, TError, TData, InfiniteData<TQueryFnData, TPageParam>, TQueryKey>['getCurrentResult'], InfiniteQueryObserverResult<TData, TError>>;
    protected fetch: ReplaceReturnType<QueryObserver<TQueryFnData, TError, TData, InfiniteData<TQueryFnData, TPageParam>, TQueryKey>['fetch'], Promise<InfiniteQueryObserverResult<TData, TError>>>;
    constructor(client: QueryClient, options: InfiniteQueryObserverOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam>);
    protected bindMethods(): void;
    setOptions(options: InfiniteQueryObserverOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam>): void;
    getOptimisticResult(options: DefaultedInfiniteQueryObserverOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam>): InfiniteQueryObserverResult<TData, TError>;
    fetchNextPage(options?: FetchNextPageOptions): Promise<InfiniteQueryObserverResult<TData, TError>>;
    fetchPreviousPage(options?: FetchPreviousPageOptions): Promise<InfiniteQueryObserverResult<TData, TError>>;
    protected createResult(query: Query<TQueryFnData, TError, InfiniteData<TQueryFnData, TPageParam>, TQueryKey>, options: InfiniteQueryObserverOptions<TQueryFnData, TError, TData, TQueryKey, TPageParam>): InfiniteQueryObserverResult<TData, TError>;
}
type ReplaceReturnType<TFunction extends (...args: Array<any>) => unknown, TReturn> = (...args: Parameters<TFunction>) => TReturn;

export { InfiniteQueryObserver };
