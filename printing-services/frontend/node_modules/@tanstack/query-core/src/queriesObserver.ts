import { notifyManager } from './notifyManager'
import { QueryObserver } from './queryObserver'
import { Subscribable } from './subscribable'
import { replaceEqualDeep, shallowEqualObjects } from './utils'
import type {
  DefaultedQueryObserverOptions,
  QueryObserverOptions,
  QueryObserverResult,
} from './types'
import type { QueryClient } from './queryClient'

function difference<T>(array1: Array<T>, array2: Array<T>): Array<T> {
  const excludeSet = new Set(array2)
  return array1.filter((x) => !excludeSet.has(x))
}

function replaceAt<T>(array: Array<T>, index: number, value: T): Array<T> {
  const copy = array.slice(0)
  copy[index] = value
  return copy
}

type QueriesObserverListener = (result: Array<QueryObserverResult>) => void

type CombineFn<TCombinedResult> = (
  result: Array<QueryObserverResult>,
) => TCombinedResult

export interface QueriesObserverOptions<
  TCombinedResult = Array<QueryObserverResult>,
> {
  combine?: CombineFn<TCombinedResult>
}

export class QueriesObserver<
  TCombinedResult = Array<QueryObserverResult>,
> extends Subscribable<QueriesObserverListener> {
  #client: QueryClient
  #result!: Array<QueryObserverResult>
  #queries: Array<QueryObserverOptions>
  #options?: QueriesObserverOptions<TCombinedResult>
  #observers: Array<QueryObserver>
  #combinedResult?: TCombinedResult
  #lastCombine?: CombineFn<TCombinedResult>
  #lastResult?: Array<QueryObserverResult>
  #observerMatches: Array<QueryObserverMatch> = []

  constructor(
    client: QueryClient,
    queries: Array<QueryObserverOptions<any, any, any, any, any>>,
    options?: QueriesObserverOptions<TCombinedResult>,
  ) {
    super()

    this.#client = client
    this.#options = options
    this.#queries = []
    this.#observers = []
    this.#result = []

    this.setQueries(queries)
  }

  protected onSubscribe(): void {
    if (this.listeners.size === 1) {
      this.#observers.forEach((observer) => {
        observer.subscribe((result) => {
          this.#onUpdate(observer, result)
        })
      })
    }
  }

  protected onUnsubscribe(): void {
    if (!this.listeners.size) {
      this.destroy()
    }
  }

  destroy(): void {
    this.listeners = new Set()
    this.#observers.forEach((observer) => {
      observer.destroy()
    })
  }

  setQueries(
    queries: Array<QueryObserverOptions>,
    options?: QueriesObserverOptions<TCombinedResult>,
  ): void {
    this.#queries = queries
    this.#options = options

    if (process.env.NODE_ENV !== 'production') {
      const queryHashes = queries.map(
        (query) => this.#client.defaultQueryOptions(query).queryHash,
      )
      if (new Set(queryHashes).size !== queryHashes.length) {
        console.warn(
          '[QueriesObserver]: Duplicate Queries found. This might result in unexpected behavior.',
        )
      }
    }

    notifyManager.batch(() => {
      const prevObservers = this.#observers

      const newObserverMatches = this.#findMatchingObservers(this.#queries)
      this.#observerMatches = newObserverMatches

      // set options for the new observers to notify of changes
      newObserverMatches.forEach((match) =>
        match.observer.setOptions(match.defaultedQueryOptions),
      )

      const newObservers = newObserverMatches.map((match) => match.observer)
      const newResult = newObservers.map((observer) =>
        observer.getCurrentResult(),
      )

      const hasLengthChange = prevObservers.length !== newObservers.length
      const hasIndexChange = newObservers.some(
        (observer, index) => observer !== prevObservers[index],
      )
      const hasStructuralChange = hasLengthChange || hasIndexChange

      const hasResultChange = hasStructuralChange
        ? true
        : newResult.some((result, index) => {
            const prev = this.#result[index]
            return !prev || !shallowEqualObjects(result, prev)
          })

      if (!hasStructuralChange && !hasResultChange) return

      if (hasStructuralChange) {
        this.#observers = newObservers
      }

      this.#result = newResult

      if (!this.hasListeners()) return

      if (hasStructuralChange) {
        difference(prevObservers, newObservers).forEach((observer) => {
          observer.destroy()
        })
        difference(newObservers, prevObservers).forEach((observer) => {
          observer.subscribe((result) => {
            this.#onUpdate(observer, result)
          })
        })
      }

      this.#notify()
    })
  }

  getCurrentResult(): Array<QueryObserverResult> {
    return this.#result
  }

  getQueries() {
    return this.#observers.map((observer) => observer.getCurrentQuery())
  }

  getObservers() {
    return this.#observers
  }

  getOptimisticResult(
    queries: Array<QueryObserverOptions>,
    combine: CombineFn<TCombinedResult> | undefined,
  ): [
    rawResult: Array<QueryObserverResult>,
    combineResult: (r?: Array<QueryObserverResult>) => TCombinedResult,
    trackResult: () => Array<QueryObserverResult>,
  ] {
    const matches = this.#findMatchingObservers(queries)
    const result = matches.map((match) =>
      match.observer.getOptimisticResult(match.defaultedQueryOptions),
    )

    return [
      result,
      (r?: Array<QueryObserverResult>) => {
        return this.#combineResult(r ?? result, combine)
      },
      () => {
        return this.#trackResult(result, matches)
      },
    ]
  }

  #trackResult(
    result: Array<QueryObserverResult>,
    matches: Array<QueryObserverMatch>,
  ) {
    return matches.map((match, index) => {
      const observerResult = result[index]!
      return !match.defaultedQueryOptions.notifyOnChangeProps
        ? match.observer.trackResult(observerResult, (accessedProp) => {
            // track property on all observers to ensure proper (synchronized) tracking (#7000)
            matches.forEach((m) => {
              m.observer.trackProp(accessedProp)
            })
          })
        : observerResult
    })
  }

  #combineResult(
    input: Array<QueryObserverResult>,
    combine: CombineFn<TCombinedResult> | undefined,
  ): TCombinedResult {
    if (combine) {
      if (
        !this.#combinedResult ||
        this.#result !== this.#lastResult ||
        combine !== this.#lastCombine
      ) {
        this.#lastCombine = combine
        this.#lastResult = this.#result
        this.#combinedResult = replaceEqualDeep(
          this.#combinedResult,
          combine(input),
        )
      }

      return this.#combinedResult
    }
    return input as any
  }

  #findMatchingObservers(
    queries: Array<QueryObserverOptions>,
  ): Array<QueryObserverMatch> {
    const prevObserversMap = new Map(
      this.#observers.map((observer) => [observer.options.queryHash, observer]),
    )

    const observers: Array<QueryObserverMatch> = []

    queries.forEach((options) => {
      const defaultedOptions = this.#client.defaultQueryOptions(options)
      const match = prevObserversMap.get(defaultedOptions.queryHash)
      if (match) {
        observers.push({
          defaultedQueryOptions: defaultedOptions,
          observer: match,
        })
      } else {
        observers.push({
          defaultedQueryOptions: defaultedOptions,
          observer: new QueryObserver(this.#client, defaultedOptions),
        })
      }
    })

    return observers
  }

  #onUpdate(observer: QueryObserver, result: QueryObserverResult): void {
    const index = this.#observers.indexOf(observer)
    if (index !== -1) {
      this.#result = replaceAt(this.#result, index, result)
      this.#notify()
    }
  }

  #notify(): void {
    if (this.hasListeners()) {
      const previousResult = this.#combinedResult
      const newTracked = this.#trackResult(this.#result, this.#observerMatches)
      const newResult = this.#combineResult(newTracked, this.#options?.combine)

      if (previousResult !== newResult) {
        notifyManager.batch(() => {
          this.listeners.forEach((listener) => {
            listener(this.#result)
          })
        })
      }
    }
  }
}

type QueryObserverMatch = {
  defaultedQueryOptions: DefaultedQueryObserverOptions
  observer: QueryObserver
}
