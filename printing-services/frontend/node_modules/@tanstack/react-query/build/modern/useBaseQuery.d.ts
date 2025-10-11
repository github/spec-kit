import { QueryKey, QueryObserver, QueryClient, QueryObserverResult } from '@tanstack/query-core';
import { UseBaseQueryOptions } from './types.js';

declare function useBaseQuery<TQueryFnData, TError, TData, TQueryData, TQueryKey extends QueryKey>(options: UseBaseQueryOptions<TQueryFnData, TError, TData, TQueryData, TQueryKey>, Observer: typeof QueryObserver, queryClient?: QueryClient): QueryObserverResult<TData, TError>;

export { useBaseQuery };
