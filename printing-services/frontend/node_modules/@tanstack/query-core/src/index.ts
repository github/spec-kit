/* istanbul ignore file */

export { focusManager } from './focusManager'
export {
  defaultShouldDehydrateMutation,
  defaultShouldDehydrateQuery,
  dehydrate,
  hydrate,
} from './hydration'
export { InfiniteQueryObserver } from './infiniteQueryObserver'
export { MutationCache } from './mutationCache'
export type { MutationCacheNotifyEvent } from './mutationCache'
export { MutationObserver } from './mutationObserver'
export { defaultScheduler, notifyManager } from './notifyManager'
export { onlineManager } from './onlineManager'
export { QueriesObserver } from './queriesObserver'
export { QueryCache } from './queryCache'
export type { QueryCacheNotifyEvent } from './queryCache'
export { QueryClient } from './queryClient'
export { QueryObserver } from './queryObserver'
export { CancelledError, isCancelledError } from './retryer'
export {
  timeoutManager,
  type ManagedTimerId,
  type TimeoutCallback,
  type TimeoutProvider,
} from './timeoutManager'
export {
  hashKey,
  isServer,
  keepPreviousData,
  matchMutation,
  matchQuery,
  noop,
  partialMatchKey,
  replaceEqualDeep,
  shouldThrowError,
  skipToken,
} from './utils'
export type { MutationFilters, QueryFilters, SkipToken, Updater } from './utils'

export { streamedQuery as experimental_streamedQuery } from './streamedQuery'

// Types
export type {
  DehydratedState,
  DehydrateOptions,
  HydrateOptions,
} from './hydration'
export { Mutation } from './mutation'
export type { MutationState } from './mutation'
export type { QueriesObserverOptions } from './queriesObserver'
export { Query } from './query'
export type { QueryState } from './query'
export * from './types'
