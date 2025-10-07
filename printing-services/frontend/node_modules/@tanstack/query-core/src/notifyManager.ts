// TYPES

import { systemSetTimeoutZero } from './timeoutManager'

type NotifyCallback = () => void

type NotifyFunction = (callback: () => void) => void

type BatchNotifyFunction = (callback: () => void) => void

type BatchCallsCallback<T extends Array<unknown>> = (...args: T) => void

type ScheduleFunction = (callback: () => void) => void

export const defaultScheduler: ScheduleFunction = systemSetTimeoutZero

export function createNotifyManager() {
  let queue: Array<NotifyCallback> = []
  let transactions = 0
  let notifyFn: NotifyFunction = (callback) => {
    callback()
  }
  let batchNotifyFn: BatchNotifyFunction = (callback: () => void) => {
    callback()
  }
  let scheduleFn = defaultScheduler

  const schedule = (callback: NotifyCallback): void => {
    if (transactions) {
      queue.push(callback)
    } else {
      scheduleFn(() => {
        notifyFn(callback)
      })
    }
  }
  const flush = (): void => {
    const originalQueue = queue
    queue = []
    if (originalQueue.length) {
      scheduleFn(() => {
        batchNotifyFn(() => {
          originalQueue.forEach((callback) => {
            notifyFn(callback)
          })
        })
      })
    }
  }

  return {
    batch: <T>(callback: () => T): T => {
      let result
      transactions++
      try {
        result = callback()
      } finally {
        transactions--
        if (!transactions) {
          flush()
        }
      }
      return result
    },
    /**
     * All calls to the wrapped function will be batched.
     */
    batchCalls: <T extends Array<unknown>>(
      callback: BatchCallsCallback<T>,
    ): BatchCallsCallback<T> => {
      return (...args) => {
        schedule(() => {
          callback(...args)
        })
      }
    },
    schedule,
    /**
     * Use this method to set a custom notify function.
     * This can be used to for example wrap notifications with `React.act` while running tests.
     */
    setNotifyFunction: (fn: NotifyFunction) => {
      notifyFn = fn
    },
    /**
     * Use this method to set a custom function to batch notifications together into a single tick.
     * By default React Query will use the batch function provided by ReactDOM or React Native.
     */
    setBatchNotifyFunction: (fn: BatchNotifyFunction) => {
      batchNotifyFn = fn
    },
    setScheduler: (fn: ScheduleFunction) => {
      scheduleFn = fn
    },
  } as const
}

// SINGLETON
export const notifyManager = createNotifyManager()
