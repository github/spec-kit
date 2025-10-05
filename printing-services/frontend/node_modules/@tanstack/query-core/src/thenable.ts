/**
 * Thenable types which matches React's types for promises
 *
 * React seemingly uses `.status`, `.value` and `.reason` properties on a promises to optimistically unwrap data from promises
 *
 * @see https://github.com/facebook/react/blob/main/packages/shared/ReactTypes.js#L112-L138
 * @see https://github.com/facebook/react/blob/4f604941569d2e8947ce1460a0b2997e835f37b9/packages/react-debug-tools/src/ReactDebugHooks.js#L224-L227
 */

import { noop } from './utils'

interface Fulfilled<T> {
  status: 'fulfilled'
  value: T
}
interface Rejected {
  status: 'rejected'
  reason: unknown
}
interface Pending<T> {
  status: 'pending'

  /**
   * Resolve the promise with a value.
   * Will remove the `resolve` and `reject` properties from the promise.
   */
  resolve: (value: T) => void
  /**
   * Reject the promise with a reason.
   * Will remove the `resolve` and `reject` properties from the promise.
   */
  reject: (reason: unknown) => void
}

export type FulfilledThenable<T> = Promise<T> & Fulfilled<T>
export type RejectedThenable<T> = Promise<T> & Rejected
export type PendingThenable<T> = Promise<T> & Pending<T>

export type Thenable<T> =
  | FulfilledThenable<T>
  | RejectedThenable<T>
  | PendingThenable<T>

export function pendingThenable<T>(): PendingThenable<T> {
  let resolve: Pending<T>['resolve']
  let reject: Pending<T>['reject']
  // this could use `Promise.withResolvers()` in the future
  const thenable = new Promise((_resolve, _reject) => {
    resolve = _resolve
    reject = _reject
  }) as PendingThenable<T>

  thenable.status = 'pending'
  thenable.catch(() => {
    // prevent unhandled rejection errors
  })

  function finalize(data: Fulfilled<T> | Rejected) {
    Object.assign(thenable, data)

    // clear pending props props to avoid calling them twice
    delete (thenable as Partial<PendingThenable<T>>).resolve
    delete (thenable as Partial<PendingThenable<T>>).reject
  }

  thenable.resolve = (value) => {
    finalize({
      status: 'fulfilled',
      value,
    })

    resolve(value)
  }
  thenable.reject = (reason) => {
    finalize({
      status: 'rejected',
      reason,
    })

    reject(reason)
  }

  return thenable
}

/**
 * This function takes a Promise-like input and detects whether the data
 * is synchronously available or not.
 *
 * It does not inspect .status, .value or .reason properties of the promise,
 * as those are not always available, and the .status of React's promises
 * should not be considered part of the public API.
 */
export function tryResolveSync(promise: Promise<unknown> | Thenable<unknown>) {
  let data: unknown

  promise
    .then((result) => {
      data = result
      return result
    }, noop)
    // .catch can be unavailable on certain kinds of thenable's
    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
    ?.catch(noop)

  if (data !== undefined) {
    return { data }
  }

  return undefined
}
