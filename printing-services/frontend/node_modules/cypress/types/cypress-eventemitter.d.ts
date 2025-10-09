// Cypress, cy, Log inherits EventEmitter.
type EventEmitter2 = import("eventemitter2").EventEmitter2

interface CyEventEmitter extends Omit<EventEmitter2, 'waitFor'> {
  proxyTo: (cy: Cypress.cy) => null
  emitMap: (eventName: string, ...args: any[]) => Array<(...args: any[]) => any>
  emitThen: (eventName: string, ...args: any[]) => Bluebird.BluebirdStatic
}

// Copied from https://github.com/DefinitelyTyped/DefinitelyTyped/blob/master/types/node/events.d.ts
// to avoid type conflict.
interface NodeEventEmitter {
  addListener(event: string | symbol, listener: (...args: any[]) => void): this
  on(event: string | symbol, listener: (...args: any[]) => void): this
  once(event: string | symbol, listener: (...args: any[]) => void): this
  removeListener(event: string | symbol, listener: (...args: any[]) => void): this
  off(event: string | symbol, listener: (...args: any[]) => void): this
  removeAllListeners(event?: string | symbol): this
  setMaxListeners(n: number): this
  getMaxListeners(): number
  listeners(event: string | symbol): Array<(...args: any[]) => void>
  rawListeners(event: string | symbol): Array<(...args: any[]) => void>
  emit(event: string | symbol, ...args: any[]): boolean
  listenerCount(type: string | symbol): number
  // Added in Node 6...
  prependListener(event: string | symbol, listener: (...args: any[]) => void): this
  prependOnceListener(event: string | symbol, listener: (...args: any[]) => void): this
  eventNames(): Array<string | symbol>
}

// We use the Buffer class for dealing with binary data, especially around the
// selectFile interface.
type BufferType = typeof import("buffer/").Buffer
