import { Subscribable } from './subscribable'
import { isServer } from './utils'

type Listener = (online: boolean) => void
type SetupFn = (setOnline: Listener) => (() => void) | undefined

export class OnlineManager extends Subscribable<Listener> {
  #online = true
  #cleanup?: () => void

  #setup: SetupFn

  constructor() {
    super()
    this.#setup = (onOnline) => {
      // addEventListener does not exist in React Native, but window does
      // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
      if (!isServer && window.addEventListener) {
        const onlineListener = () => onOnline(true)
        const offlineListener = () => onOnline(false)
        // Listen to online
        window.addEventListener('online', onlineListener, false)
        window.addEventListener('offline', offlineListener, false)

        return () => {
          // Be sure to unsubscribe if a new handler is set
          window.removeEventListener('online', onlineListener)
          window.removeEventListener('offline', offlineListener)
        }
      }

      return
    }
  }

  protected onSubscribe(): void {
    if (!this.#cleanup) {
      this.setEventListener(this.#setup)
    }
  }

  protected onUnsubscribe() {
    if (!this.hasListeners()) {
      this.#cleanup?.()
      this.#cleanup = undefined
    }
  }

  setEventListener(setup: SetupFn): void {
    this.#setup = setup
    this.#cleanup?.()
    this.#cleanup = setup(this.setOnline.bind(this))
  }

  setOnline(online: boolean): void {
    const changed = this.#online !== online

    if (changed) {
      this.#online = online
      this.listeners.forEach((listener) => {
        listener(online)
      })
    }
  }

  isOnline(): boolean {
    return this.#online
  }
}

export const onlineManager = new OnlineManager()
