'use client'
import * as React from 'react'

import { hydrate } from '@tanstack/query-core'
import { useQueryClient } from './QueryClientProvider'
import type {
  DehydratedState,
  HydrateOptions,
  OmitKeyof,
  QueryClient,
} from '@tanstack/query-core'

export interface HydrationBoundaryProps {
  state: DehydratedState | null | undefined
  options?: OmitKeyof<HydrateOptions, 'defaultOptions'> & {
    defaultOptions?: OmitKeyof<
      Exclude<HydrateOptions['defaultOptions'], undefined>,
      'mutations'
    >
  }
  children?: React.ReactNode
  queryClient?: QueryClient
}

export const HydrationBoundary = ({
  children,
  options = {},
  state,
  queryClient,
}: HydrationBoundaryProps) => {
  const client = useQueryClient(queryClient)

  const optionsRef = React.useRef(options)
  optionsRef.current = options

  // This useMemo is for performance reasons only, everything inside it must
  // be safe to run in every render and code here should be read as "in render".
  //
  // This code needs to happen during the render phase, because after initial
  // SSR, hydration needs to happen _before_ children render. Also, if hydrating
  // during a transition, we want to hydrate as much as is safe in render so
  // we can prerender as much as possible.
  //
  // For any queries that already exist in the cache, we want to hold back on
  // hydrating until _after_ the render phase. The reason for this is that during
  // transitions, we don't want the existing queries and observers to update to
  // the new data on the current page, only _after_ the transition is committed.
  // If the transition is aborted, we will have hydrated any _new_ queries, but
  // we throw away the fresh data for any existing ones to avoid unexpectedly
  // updating the UI.
  const hydrationQueue: DehydratedState['queries'] | undefined =
    React.useMemo(() => {
      if (state) {
        if (typeof state !== 'object') {
          return
        }

        const queryCache = client.getQueryCache()
        // State is supplied from the outside and we might as well fail
        // gracefully if it has the wrong shape, so while we type `queries`
        // as required, we still provide a fallback.
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
        const queries = state.queries || []

        const newQueries: DehydratedState['queries'] = []
        const existingQueries: DehydratedState['queries'] = []
        for (const dehydratedQuery of queries) {
          const existingQuery = queryCache.get(dehydratedQuery.queryHash)

          if (!existingQuery) {
            newQueries.push(dehydratedQuery)
          } else {
            const hydrationIsNewer =
              dehydratedQuery.state.dataUpdatedAt >
                existingQuery.state.dataUpdatedAt ||
              (dehydratedQuery.promise &&
                existingQuery.state.status !== 'pending' &&
                existingQuery.state.fetchStatus !== 'fetching' &&
                dehydratedQuery.dehydratedAt !== undefined &&
                dehydratedQuery.dehydratedAt >
                  existingQuery.state.dataUpdatedAt)

            if (hydrationIsNewer) {
              existingQueries.push(dehydratedQuery)
            }
          }
        }

        if (newQueries.length > 0) {
          // It's actually fine to call this with queries/state that already exists
          // in the cache, or is older. hydrate() is idempotent for queries.
          hydrate(client, { queries: newQueries }, optionsRef.current)
        }
        if (existingQueries.length > 0) {
          return existingQueries
        }
      }
      return undefined
    }, [client, state])

  React.useEffect(() => {
    if (hydrationQueue) {
      hydrate(client, { queries: hydrationQueue }, optionsRef.current)
    }
  }, [client, hydrationQueue])

  return children as React.ReactElement
}
