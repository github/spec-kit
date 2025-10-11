import { UseMutationOptions, UseMutationResult } from './types.cjs';
import { DefaultError, QueryClient } from '@tanstack/query-core';

declare function useMutation<TData = unknown, TError = DefaultError, TVariables = void, TOnMutateResult = unknown>(options: UseMutationOptions<TData, TError, TVariables, TOnMutateResult>, queryClient?: QueryClient): UseMutationResult<TData, TError, TVariables, TOnMutateResult>;

export { useMutation };
