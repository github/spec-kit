/* istanbul ignore file */

// Re-export core
export * from '@tanstack/query-core'

// React Query
export * from './types'
export { useQueries } from './useQueries'
export type { QueriesResults, QueriesOptions } from './useQueries'
export { useQuery } from './useQuery'
export { useSuspenseQuery } from './useSuspenseQuery'
export { useSuspenseInfiniteQuery } from './useSuspenseInfiniteQuery'
export { useSuspenseQueries } from './useSuspenseQueries'
export type {
  SuspenseQueriesResults,
  SuspenseQueriesOptions,
} from './useSuspenseQueries'
export { usePrefetchQuery } from './usePrefetchQuery'
export { usePrefetchInfiniteQuery } from './usePrefetchInfiniteQuery'
export { queryOptions } from './queryOptions'
export type {
  DefinedInitialDataOptions,
  UndefinedInitialDataOptions,
  UnusedSkipTokenOptions,
} from './queryOptions'
export { infiniteQueryOptions } from './infiniteQueryOptions'
export type {
  DefinedInitialDataInfiniteOptions,
  UndefinedInitialDataInfiniteOptions,
  UnusedSkipTokenInfiniteOptions,
} from './infiniteQueryOptions'
export {
  QueryClientContext,
  QueryClientProvider,
  useQueryClient,
} from './QueryClientProvider'
export type { QueryClientProviderProps } from './QueryClientProvider'
export type { QueryErrorResetBoundaryProps } from './QueryErrorResetBoundary'
export { HydrationBoundary } from './HydrationBoundary'
export type { HydrationBoundaryProps } from './HydrationBoundary'
export type {
  QueryErrorClearResetFunction,
  QueryErrorIsResetFunction,
  QueryErrorResetBoundaryFunction,
  QueryErrorResetFunction,
} from './QueryErrorResetBoundary'
export {
  QueryErrorResetBoundary,
  useQueryErrorResetBoundary,
} from './QueryErrorResetBoundary'
export { useIsFetching } from './useIsFetching'
export { useIsMutating, useMutationState } from './useMutationState'
export { useMutation } from './useMutation'
export { mutationOptions } from './mutationOptions'
export { useInfiniteQuery } from './useInfiniteQuery'
export { useIsRestoring, IsRestoringProvider } from './IsRestoringProvider'
