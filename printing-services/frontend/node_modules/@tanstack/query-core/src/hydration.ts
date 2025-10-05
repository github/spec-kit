import { tryResolveSync } from './thenable'
import type {
  DefaultError,
  MutationKey,
  MutationMeta,
  MutationOptions,
  MutationScope,
  QueryKey,
  QueryMeta,
  QueryOptions,
} from './types'
import type { QueryClient } from './queryClient'
import type { Query, QueryState } from './query'
import type { Mutation, MutationState } from './mutation'

// TYPES
type TransformerFn = (data: any) => any
function defaultTransformerFn(data: any): any {
  return data
}

export interface DehydrateOptions {
  serializeData?: TransformerFn
  shouldDehydrateMutation?: (mutation: Mutation) => boolean
  shouldDehydrateQuery?: (query: Query) => boolean
  shouldRedactErrors?: (error: unknown) => boolean
}

export interface HydrateOptions {
  defaultOptions?: {
    deserializeData?: TransformerFn
    queries?: QueryOptions
    mutations?: MutationOptions<unknown, DefaultError, unknown, unknown>
  }
}

interface DehydratedMutation {
  mutationKey?: MutationKey
  state: MutationState
  meta?: MutationMeta
  scope?: MutationScope
}

interface DehydratedQuery {
  queryHash: string
  queryKey: QueryKey
  state: QueryState
  promise?: Promise<unknown>
  meta?: QueryMeta
  // This is only optional because older versions of Query might have dehydrated
  // without it which we need to handle for backwards compatibility.
  // This should be changed to required in the future.
  dehydratedAt?: number
}

export interface DehydratedState {
  mutations: Array<DehydratedMutation>
  queries: Array<DehydratedQuery>
}

// FUNCTIONS

function dehydrateMutation(mutation: Mutation): DehydratedMutation {
  return {
    mutationKey: mutation.options.mutationKey,
    state: mutation.state,
    ...(mutation.options.scope && { scope: mutation.options.scope }),
    ...(mutation.meta && { meta: mutation.meta }),
  }
}

// Most config is not dehydrated but instead meant to configure again when
// consuming the de/rehydrated data, typically with useQuery on the client.
// Sometimes it might make sense to prefetch data on the server and include
// in the html-payload, but not consume it on the initial render.
function dehydrateQuery(
  query: Query,
  serializeData: TransformerFn,
  shouldRedactErrors: (error: unknown) => boolean,
): DehydratedQuery {
  return {
    dehydratedAt: Date.now(),
    state: {
      ...query.state,
      ...(query.state.data !== undefined && {
        data: serializeData(query.state.data),
      }),
    },
    queryKey: query.queryKey,
    queryHash: query.queryHash,
    ...(query.state.status === 'pending' && {
      promise: query.promise?.then(serializeData).catch((error) => {
        if (!shouldRedactErrors(error)) {
          // Reject original error if it should not be redacted
          return Promise.reject(error)
        }
        // If not in production, log original error before rejecting redacted error
        if (process.env.NODE_ENV !== 'production') {
          console.error(
            `A query that was dehydrated as pending ended up rejecting. [${query.queryHash}]: ${error}; The error will be redacted in production builds`,
          )
        }
        return Promise.reject(new Error('redacted'))
      }),
    }),
    ...(query.meta && { meta: query.meta }),
  }
}

export function defaultShouldDehydrateMutation(mutation: Mutation) {
  return mutation.state.isPaused
}

export function defaultShouldDehydrateQuery(query: Query) {
  return query.state.status === 'success'
}

function defaultShouldRedactErrors(_: unknown) {
  return true
}

export function dehydrate(
  client: QueryClient,
  options: DehydrateOptions = {},
): DehydratedState {
  const filterMutation =
    options.shouldDehydrateMutation ??
    client.getDefaultOptions().dehydrate?.shouldDehydrateMutation ??
    defaultShouldDehydrateMutation

  const mutations = client
    .getMutationCache()
    .getAll()
    .flatMap((mutation) =>
      filterMutation(mutation) ? [dehydrateMutation(mutation)] : [],
    )

  const filterQuery =
    options.shouldDehydrateQuery ??
    client.getDefaultOptions().dehydrate?.shouldDehydrateQuery ??
    defaultShouldDehydrateQuery

  const shouldRedactErrors =
    options.shouldRedactErrors ??
    client.getDefaultOptions().dehydrate?.shouldRedactErrors ??
    defaultShouldRedactErrors

  const serializeData =
    options.serializeData ??
    client.getDefaultOptions().dehydrate?.serializeData ??
    defaultTransformerFn

  const queries = client
    .getQueryCache()
    .getAll()
    .flatMap((query) =>
      filterQuery(query)
        ? [dehydrateQuery(query, serializeData, shouldRedactErrors)]
        : [],
    )

  return { mutations, queries }
}

export function hydrate(
  client: QueryClient,
  dehydratedState: unknown,
  options?: HydrateOptions,
): void {
  if (typeof dehydratedState !== 'object' || dehydratedState === null) {
    return
  }

  const mutationCache = client.getMutationCache()
  const queryCache = client.getQueryCache()
  const deserializeData =
    options?.defaultOptions?.deserializeData ??
    client.getDefaultOptions().hydrate?.deserializeData ??
    defaultTransformerFn

  // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
  const mutations = (dehydratedState as DehydratedState).mutations || []
  // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
  const queries = (dehydratedState as DehydratedState).queries || []

  mutations.forEach(({ state, ...mutationOptions }) => {
    mutationCache.build(
      client,
      {
        ...client.getDefaultOptions().hydrate?.mutations,
        ...options?.defaultOptions?.mutations,
        ...mutationOptions,
      },
      state,
    )
  })

  queries.forEach(
    ({ queryKey, state, queryHash, meta, promise, dehydratedAt }) => {
      const syncData = promise ? tryResolveSync(promise) : undefined
      const rawData = state.data === undefined ? syncData?.data : state.data
      const data = rawData === undefined ? rawData : deserializeData(rawData)

      let query = queryCache.get(queryHash)
      const existingQueryIsPending = query?.state.status === 'pending'
      const existingQueryIsFetching = query?.state.fetchStatus === 'fetching'

      // Do not hydrate if an existing query exists with newer data
      if (query) {
        const hasNewerSyncData =
          syncData &&
          // We only need this undefined check to handle older dehydration
          // payloads that might not have dehydratedAt
          dehydratedAt !== undefined &&
          dehydratedAt > query.state.dataUpdatedAt
        if (
          state.dataUpdatedAt > query.state.dataUpdatedAt ||
          hasNewerSyncData
        ) {
          // omit fetchStatus from dehydrated state
          // so that query stays in its current fetchStatus
          const { fetchStatus: _ignored, ...serializedState } = state
          query.setState({
            ...serializedState,
            data,
          })
        }
      } else {
        // Restore query
        query = queryCache.build(
          client,
          {
            ...client.getDefaultOptions().hydrate?.queries,
            ...options?.defaultOptions?.queries,
            queryKey,
            queryHash,
            meta,
          },
          // Reset fetch status to idle to avoid
          // query being stuck in fetching state upon hydration
          {
            ...state,
            data,
            fetchStatus: 'idle',
            status: data !== undefined ? 'success' : state.status,
          },
        )
      }

      if (
        promise &&
        !existingQueryIsPending &&
        !existingQueryIsFetching &&
        // Only hydrate if dehydration is newer than any existing data,
        // this is always true for new queries
        (dehydratedAt === undefined || dehydratedAt > query.state.dataUpdatedAt)
      ) {
        // This doesn't actually fetch - it just creates a retryer
        // which will re-use the passed `initialPromise`
        // Note that we need to call these even when data was synchronously
        // available, as we still need to set up the retryer
        void query.fetch(undefined, {
          // RSC transformed promises are not thenable
          initialPromise: Promise.resolve(promise).then(deserializeData),
        })
      }
    },
  )
}
