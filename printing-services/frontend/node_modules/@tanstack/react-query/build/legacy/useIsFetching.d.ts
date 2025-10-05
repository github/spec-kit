import { QueryFilters, QueryClient } from '@tanstack/query-core';

declare function useIsFetching(filters?: QueryFilters, queryClient?: QueryClient): number;

export { useIsFetching };
