import { timeoutManager } from './timeoutManager'
import { isServer, isValidTimeout } from './utils'
import type { ManagedTimerId } from './timeoutManager'

export abstract class Removable {
  gcTime!: number
  #gcTimeout?: ManagedTimerId

  destroy(): void {
    this.clearGcTimeout()
  }

  protected scheduleGc(): void {
    this.clearGcTimeout()

    if (isValidTimeout(this.gcTime)) {
      this.#gcTimeout = timeoutManager.setTimeout(() => {
        this.optionalRemove()
      }, this.gcTime)
    }
  }

  protected updateGcTime(newGcTime: number | undefined): void {
    // Default to 5 minutes (Infinity for server-side) if no gcTime is set
    this.gcTime = Math.max(
      this.gcTime || 0,
      newGcTime ?? (isServer ? Infinity : 5 * 60 * 1000),
    )
  }

  protected clearGcTimeout() {
    if (this.#gcTimeout) {
      timeoutManager.clearTimeout(this.#gcTimeout)
      this.#gcTimeout = undefined
    }
  }

  protected abstract optionalRemove(): void
}
