import { addToEnd, addToStart, ensureQueryFn } from './utils'
import type { QueryBehavior } from './query'
import type {
  InfiniteData,
  InfiniteQueryPageParamsOptions,
  OmitKeyof,
  QueryFunctionContext,
  QueryKey,
} from './types'

export function infiniteQueryBehavior<TQueryFnData, TError, TData, TPageParam>(
  pages?: number,
): QueryBehavior<TQueryFnData, TError, InfiniteData<TData, TPageParam>> {
  return {
    onFetch: (context, query) => {
      const options = context.options as InfiniteQueryPageParamsOptions<TData>
      const direction = context.fetchOptions?.meta?.fetchMore?.direction
      const oldPages = context.state.data?.pages || []
      const oldPageParams = context.state.data?.pageParams || []
      let result: InfiniteData<unknown> = { pages: [], pageParams: [] }
      let currentPage = 0

      const fetchFn = async () => {
        let cancelled = false
        const addSignalProperty = (object: unknown) => {
          Object.defineProperty(object, 'signal', {
            enumerable: true,
            get: () => {
              if (context.signal.aborted) {
                cancelled = true
              } else {
                context.signal.addEventListener('abort', () => {
                  cancelled = true
                })
              }
              return context.signal
            },
          })
        }

        const queryFn = ensureQueryFn(context.options, context.fetchOptions)

        // Create function to fetch a page
        const fetchPage = async (
          data: InfiniteData<unknown>,
          param: unknown,
          previous?: boolean,
        ): Promise<InfiniteData<unknown>> => {
          if (cancelled) {
            return Promise.reject()
          }

          if (param == null && data.pages.length) {
            return Promise.resolve(data)
          }

          const createQueryFnContext = () => {
            const queryFnContext: OmitKeyof<
              QueryFunctionContext<QueryKey, unknown>,
              'signal'
            > = {
              client: context.client,
              queryKey: context.queryKey,
              pageParam: param,
              direction: previous ? 'backward' : 'forward',
              meta: context.options.meta,
            }
            addSignalProperty(queryFnContext)
            return queryFnContext as QueryFunctionContext<QueryKey, unknown>
          }

          const queryFnContext = createQueryFnContext()

          const page = await queryFn(queryFnContext)

          const { maxPages } = context.options
          const addTo = previous ? addToStart : addToEnd

          return {
            pages: addTo(data.pages, page, maxPages),
            pageParams: addTo(data.pageParams, param, maxPages),
          }
        }

        // fetch next / previous page?
        if (direction && oldPages.length) {
          const previous = direction === 'backward'
          const pageParamFn = previous ? getPreviousPageParam : getNextPageParam
          const oldData = {
            pages: oldPages,
            pageParams: oldPageParams,
          }
          const param = pageParamFn(options, oldData)

          result = await fetchPage(oldData, param, previous)
        } else {
          const remainingPages = pages ?? oldPages.length

          // Fetch all pages
          do {
            const param =
              currentPage === 0
                ? (oldPageParams[0] ?? options.initialPageParam)
                : getNextPageParam(options, result)
            if (currentPage > 0 && param == null) {
              break
            }
            result = await fetchPage(result, param)
            currentPage++
          } while (currentPage < remainingPages)
        }

        return result
      }
      if (context.options.persister) {
        context.fetchFn = () => {
          return context.options.persister?.(
            fetchFn as any,
            {
              client: context.client,
              queryKey: context.queryKey,
              meta: context.options.meta,
              signal: context.signal,
            },
            query,
          )
        }
      } else {
        context.fetchFn = fetchFn
      }
    },
  }
}

function getNextPageParam(
  options: InfiniteQueryPageParamsOptions<any>,
  { pages, pageParams }: InfiniteData<unknown>,
): unknown | undefined {
  const lastIndex = pages.length - 1
  return pages.length > 0
    ? options.getNextPageParam(
        pages[lastIndex],
        pages,
        pageParams[lastIndex],
        pageParams,
      )
    : undefined
}

function getPreviousPageParam(
  options: InfiniteQueryPageParamsOptions<any>,
  { pages, pageParams }: InfiniteData<unknown>,
): unknown | undefined {
  return pages.length > 0
    ? options.getPreviousPageParam?.(pages[0], pages, pageParams[0], pageParams)
    : undefined
}

/**
 * Checks if there is a next page.
 */
export function hasNextPage(
  options: InfiniteQueryPageParamsOptions<any, any>,
  data?: InfiniteData<unknown>,
): boolean {
  if (!data) return false
  return getNextPageParam(options, data) != null
}

/**
 * Checks if there is a previous page.
 */
export function hasPreviousPage(
  options: InfiniteQueryPageParamsOptions<any, any>,
  data?: InfiniteData<unknown>,
): boolean {
  if (!data || !options.getPreviousPageParam) return false
  return getPreviousPageParam(options, data) != null
}
