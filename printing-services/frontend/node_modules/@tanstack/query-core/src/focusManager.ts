import { Subscribable } from './subscribable'
import { isServer } from './utils'

type Listener = (focused: boolean) => void

type SetupFn = (
  setFocused: (focused?: boolean) => void,
) => (() => void) | undefined

export class FocusManager extends Subscribable<Listener> {
  #focused?: boolean
  #cleanup?: () => void

  #setup: SetupFn

  constructor() {
    super()
    this.#setup = (onFocus) => {
      // addEventListener does not exist in React Native, but window does
      // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
      if (!isServer && window.addEventListener) {
        const listener = () => onFocus()
        // Listen to visibilitychange
        window.addEventListener('visibilitychange', listener, false)

        return () => {
          // Be sure to unsubscribe if a new handler is set
          window.removeEventListener('visibilitychange', listener)
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
    this.#cleanup = setup((focused) => {
      if (typeof focused === 'boolean') {
        this.setFocused(focused)
      } else {
        this.onFocus()
      }
    })
  }

  setFocused(focused?: boolean): void {
    const changed = this.#focused !== focused
    if (changed) {
      this.#focused = focused
      this.onFocus()
    }
  }

  onFocus(): void {
    const isFocused = this.isFocused()
    this.listeners.forEach((listener) => {
      listener(isFocused)
    })
  }

  isFocused(): boolean {
    if (typeof this.#focused === 'boolean') {
      return this.#focused
    }

    // document global can be unavailable in react native
    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
    return globalThis.document?.visibilityState !== 'hidden'
  }
}

export const focusManager = new FocusManager()
