import { DefaultError, WithRequired } from '@tanstack/query-core';
import { UseMutationOptions } from './types.js';

declare function mutationOptions<TData = unknown, TError = DefaultError, TVariables = void, TOnMutateResult = unknown>(options: WithRequired<UseMutationOptions<TData, TError, TVariables, TOnMutateResult>, 'mutationKey'>): WithRequired<UseMutationOptions<TData, TError, TVariables, TOnMutateResult>, 'mutationKey'>;
declare function mutationOptions<TData = unknown, TError = DefaultError, TVariables = void, TOnMutateResult = unknown>(options: Omit<UseMutationOptions<TData, TError, TVariables, TOnMutateResult>, 'mutationKey'>): Omit<UseMutationOptions<TData, TError, TVariables, TOnMutateResult>, 'mutationKey'>;

export { mutationOptions };
