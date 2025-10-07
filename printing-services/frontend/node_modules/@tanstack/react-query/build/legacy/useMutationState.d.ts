import { MutationFilters, QueryClient, MutationState, Mutation } from '@tanstack/query-core';

declare function useIsMutating(filters?: MutationFilters, queryClient?: QueryClient): number;
type MutationStateOptions<TResult = MutationState> = {
    filters?: MutationFilters;
    select?: (mutation: Mutation) => TResult;
};
declare function useMutationState<TResult = MutationState>(options?: MutationStateOptions<TResult>, queryClient?: QueryClient): Array<TResult>;

export { useIsMutating, useMutationState };
