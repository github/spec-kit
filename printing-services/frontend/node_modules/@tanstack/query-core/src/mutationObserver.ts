import { getDefaultState } from './mutation'
import { notifyManager } from './notifyManager'
import { Subscribable } from './subscribable'
import { hashKey, shallowEqualObjects } from './utils'
import type { QueryClient } from './queryClient'
import type {
  DefaultError,
  MutateOptions,
  MutationFunctionContext,
  MutationObserverOptions,
  MutationObserverResult,
} from './types'
import type { Action, Mutation } from './mutation'

// TYPES

type MutationObserverListener<TData, TError, TVariables, TOnMutateResult> = (
  result: MutationObserverResult<TData, TError, TVariables, TOnMutateResult>,
) => void

// CLASS

export class MutationObserver<
  TData = unknown,
  TError = DefaultError,
  TVariables = void,
  TOnMutateResult = unknown,
> extends Subscribable<
  MutationObserverListener<TData, TError, TVariables, TOnMutateResult>
> {
  options!: MutationObserverOptions<TData, TError, TVariables, TOnMutateResult>

  #client: QueryClient
  #currentResult: MutationObserverResult<
    TData,
    TError,
    TVariables,
    TOnMutateResult
  > = undefined!
  #currentMutation?: Mutation<TData, TError, TVariables, TOnMutateResult>
  #mutateOptions?: MutateOptions<TData, TError, TVariables, TOnMutateResult>

  constructor(
    client: QueryClient,
    options: MutationObserverOptions<
      TData,
      TError,
      TVariables,
      TOnMutateResult
    >,
  ) {
    super()

    this.#client = client
    this.setOptions(options)
    this.bindMethods()
    this.#updateResult()
  }

  protected bindMethods(): void {
    this.mutate = this.mutate.bind(this)
    this.reset = this.reset.bind(this)
  }

  setOptions(
    options: MutationObserverOptions<
      TData,
      TError,
      TVariables,
      TOnMutateResult
    >,
  ) {
    const prevOptions = this.options as
      | MutationObserverOptions<TData, TError, TVariables, TOnMutateResult>
      | undefined
    this.options = this.#client.defaultMutationOptions(options)
    if (!shallowEqualObjects(this.options, prevOptions)) {
      this.#client.getMutationCache().notify({
        type: 'observerOptionsUpdated',
        mutation: this.#currentMutation,
        observer: this,
      })
    }

    if (
      prevOptions?.mutationKey &&
      this.options.mutationKey &&
      hashKey(prevOptions.mutationKey) !== hashKey(this.options.mutationKey)
    ) {
      this.reset()
    } else if (this.#currentMutation?.state.status === 'pending') {
      this.#currentMutation.setOptions(this.options)
    }
  }

  protected onUnsubscribe(): void {
    if (!this.hasListeners()) {
      this.#currentMutation?.removeObserver(this)
    }
  }

  onMutationUpdate(
    action: Action<TData, TError, TVariables, TOnMutateResult>,
  ): void {
    this.#updateResult()

    this.#notify(action)
  }

  getCurrentResult(): MutationObserverResult<
    TData,
    TError,
    TVariables,
    TOnMutateResult
  > {
    return this.#currentResult
  }

  reset(): void {
    // reset needs to remove the observer from the mutation because there is no way to "get it back"
    // another mutate call will yield a new mutation!
    this.#currentMutation?.removeObserver(this)
    this.#currentMutation = undefined
    this.#updateResult()
    this.#notify()
  }

  mutate(
    variables: TVariables,
    options?: MutateOptions<TData, TError, TVariables, TOnMutateResult>,
  ): Promise<TData> {
    this.#mutateOptions = options

    this.#currentMutation?.removeObserver(this)

    this.#currentMutation = this.#client
      .getMutationCache()
      .build(this.#client, this.options)

    this.#currentMutation.addObserver(this)

    return this.#currentMutation.execute(variables)
  }

  #updateResult(): void {
    const state =
      this.#currentMutation?.state ??
      getDefaultState<TData, TError, TVariables, TOnMutateResult>()

    this.#currentResult = {
      ...state,
      isPending: state.status === 'pending',
      isSuccess: state.status === 'success',
      isError: state.status === 'error',
      isIdle: state.status === 'idle',
      mutate: this.mutate,
      reset: this.reset,
    } as MutationObserverResult<TData, TError, TVariables, TOnMutateResult>
  }

  #notify(action?: Action<TData, TError, TVariables, TOnMutateResult>): void {
    notifyManager.batch(() => {
      // First trigger the mutate callbacks
      if (this.#mutateOptions && this.hasListeners()) {
        const variables = this.#currentResult.variables!
        const onMutateResult = this.#currentResult.context

        const context = {
          client: this.#client,
          meta: this.options.meta,
          mutationKey: this.options.mutationKey,
        } satisfies MutationFunctionContext

        if (action?.type === 'success') {
          this.#mutateOptions.onSuccess?.(
            action.data,
            variables,
            onMutateResult,
            context,
          )
          this.#mutateOptions.onSettled?.(
            action.data,
            null,
            variables,
            onMutateResult,
            context,
          )
        } else if (action?.type === 'error') {
          this.#mutateOptions.onError?.(
            action.error,
            variables,
            onMutateResult,
            context,
          )
          this.#mutateOptions.onSettled?.(
            undefined,
            action.error,
            variables,
            onMutateResult,
            context,
          )
        }
      }

      // Then trigger the listeners
      this.listeners.forEach((listener) => {
        listener(this.#currentResult)
      })
    })
  }
}
