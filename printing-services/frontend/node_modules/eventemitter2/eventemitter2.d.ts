export type event = (symbol|string);
export type eventNS = string|event[];

export interface ConstructorOptions {
    /**
     * @default false
     * @description set this to `true` to use wildcards.
     */
    wildcard?: boolean,
    /**
     * @default '.'
     * @description the delimiter used to segment namespaces.
     */
    delimiter?: string,
    /**
     * @default false
     * @description set this to `true` if you want to emit the newListener events.
     */
    newListener?: boolean,
    /**
     * @default false
     * @description set this to `true` if you want to emit the removeListener events.
     */
    removeListener?: boolean,
    /**
     * @default 10
     * @description the maximum amount of listeners that can be assigned to an event.
     */
    maxListeners?: number
    /**
     * @default false
     * @description show event name in memory leak message when more than maximum amount of listeners is assigned, default false
     */
    verboseMemoryLeak?: boolean
    /**
     * @default false
     * @description disable throwing uncaughtException if an error event is emitted and it has no listeners
     */
    ignoreErrors?: boolean
}
export interface ListenerFn {
    (...values: any[]): void;
}
export interface EventAndListener {
    (event: string | string[], ...values: any[]): void;
}

export interface WaitForFilter { (...values: any[]): boolean }

export interface WaitForOptions {
    /**
     * @default 0
     */
    timeout: number,
    /**
     * @default null
     */
    filter: WaitForFilter,
    /**
     * @default false
     */
    handleError: boolean,
    /**
     * @default Promise
     */
    Promise: Function,
    /**
     * @default false
     */
    overload: boolean
}

export interface CancelablePromise<T> extends Promise<T>{
    cancel(reason: string): undefined
}

export interface OnceOptions {
    /**
     * @default 0
     */
    timeout: number,
    /**
     * @default Promise
     */
    Promise: Function,
    /**
     * @default false
     */
    overload: boolean
}

export interface ListenToOptions {
    on?: { (event: event | eventNS, handler: ListenerFn): void },
    off?: { (event: event | eventNS, handler: ListenerFn): void },
    reducers: Function | Object
}

export interface GeneralEventEmitter{
    addEventListener(event: event, handler: ListenerFn): this,
    removeEventListener(event: event, handler: ListenerFn): this,
    addListener?(event: event, handler: ListenerFn): this,
    removeListener?(event: event, handler: ListenerFn): this,
    on?(event: event, handler: ListenerFn): this,
    off?(event: event, handler: ListenerFn): this
}

export interface OnOptions {
    async?: boolean,
    promisify?: boolean,
    nextTick?: boolean,
    objectify?: boolean
}

export interface Listener {
    emitter: EventEmitter2;
    event: event|eventNS;
    listener: ListenerFn;
    off(): this;
}

export declare class EventEmitter2 {
    constructor(options?: ConstructorOptions)
    emit(event: event | eventNS, ...values: any[]): boolean;
    emitAsync(event: event | eventNS, ...values: any[]): Promise<any[]>;
    addListener(event: event | eventNS, listener: ListenerFn): this|Listener;
    on(event: event | eventNS, listener: ListenerFn, options?: boolean|OnOptions): this|Listener;
    prependListener(event: event | eventNS, listener: ListenerFn, options?: boolean|OnOptions): this|Listener;
    once(event: event | eventNS, listener: ListenerFn, options?: true|OnOptions): this|Listener;
    prependOnceListener(event: event | eventNS, listener: ListenerFn, options?: boolean|OnOptions): this|Listener;
    many(event: event | eventNS, timesToListen: number, listener: ListenerFn, options?: boolean|OnOptions): this|Listener;
    prependMany(event: event | eventNS, timesToListen: number, listener: ListenerFn, options?: boolean|OnOptions): this|Listener;
    onAny(listener: EventAndListener): this;
    prependAny(listener: EventAndListener): this;
    offAny(listener: ListenerFn): this;
    removeListener(event: event | eventNS, listener: ListenerFn): this;
    off(event: event | eventNS, listener: ListenerFn): this;
    removeAllListeners(event?: event | eventNS): this;
    setMaxListeners(n: number): void;
    getMaxListeners(): number;
    eventNames(nsAsArray?: boolean): (event|eventNS)[];
    listenerCount(event?: event | eventNS): number
    listeners(event?: event | eventNS): ListenerFn[]
    listenersAny(): ListenerFn[]
    waitFor(event: event | eventNS, timeout?: number): CancelablePromise<any[]>
    waitFor(event: event | eventNS, filter?: WaitForFilter): CancelablePromise<any[]>
    waitFor(event: event | eventNS, options?: WaitForOptions): CancelablePromise<any[]>
    listenTo(target: GeneralEventEmitter, events: event | eventNS, options?: ListenToOptions): this;
    listenTo(target: GeneralEventEmitter, events: event[], options?: ListenToOptions): this;
    listenTo(target: GeneralEventEmitter, events: Object, options?: ListenToOptions): this;
    stopListeningTo(target?: GeneralEventEmitter, event?: event | eventNS): Boolean;
    hasListeners(event?: String): Boolean
    static once(emitter: EventEmitter2, event: event | eventNS, options?: OnceOptions): CancelablePromise<any[]>;
    static defaultMaxListeners: number;
}

export default EventEmitter2;
