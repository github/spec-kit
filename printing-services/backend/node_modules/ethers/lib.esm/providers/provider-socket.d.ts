/**
 *  Generic long-lived socket provider.
 *
 *  Sub-classing notes
 *  - a sub-class MUST call the `_start()` method once connected
 *  - a sub-class MUST override the `_write(string)` method
 *  - a sub-class MUST call `_processMessage(string)` for each message
 *
 *  @_subsection: api/providers/abstract-provider:Socket Providers  [about-socketProvider]
 */
import { JsonRpcApiProvider } from "./provider-jsonrpc.js";
import type { Subscriber, Subscription } from "./abstract-provider.js";
import type { EventFilter } from "./provider.js";
import type { JsonRpcApiProviderOptions, JsonRpcError, JsonRpcPayload, JsonRpcResult } from "./provider-jsonrpc.js";
import type { Networkish } from "./network.js";
/**
 *  A **SocketSubscriber** uses a socket transport to handle events and
 *  should use [[_emit]] to manage the events.
 */
export declare class SocketSubscriber implements Subscriber {
    #private;
    /**
     *  The filter.
     */
    get filter(): Array<any>;
    /**
     *  Creates a new **SocketSubscriber** attached to %%provider%% listening
     *  to %%filter%%.
     */
    constructor(provider: SocketProvider, filter: Array<any>);
    start(): void;
    stop(): void;
    pause(dropWhilePaused?: boolean): void;
    resume(): void;
    /**
     *  @_ignore:
     */
    _handleMessage(message: any): void;
    /**
     *  Sub-classes **must** override this to emit the events on the
     *  provider.
     */
    _emit(provider: SocketProvider, message: any): Promise<void>;
}
/**
 *  A **SocketBlockSubscriber** listens for ``newHeads`` events and emits
 *  ``"block"`` events.
 */
export declare class SocketBlockSubscriber extends SocketSubscriber {
    /**
     *  @_ignore:
     */
    constructor(provider: SocketProvider);
    _emit(provider: SocketProvider, message: any): Promise<void>;
}
/**
 *  A **SocketPendingSubscriber** listens for pending transacitons and emits
 *  ``"pending"`` events.
 */
export declare class SocketPendingSubscriber extends SocketSubscriber {
    /**
     *  @_ignore:
     */
    constructor(provider: SocketProvider);
    _emit(provider: SocketProvider, message: any): Promise<void>;
}
/**
 *  A **SocketEventSubscriber** listens for event logs.
 */
export declare class SocketEventSubscriber extends SocketSubscriber {
    #private;
    /**
     *  The filter.
     */
    get logFilter(): EventFilter;
    /**
     *  @_ignore:
     */
    constructor(provider: SocketProvider, filter: EventFilter);
    _emit(provider: SocketProvider, message: any): Promise<void>;
}
/**
 *  A **SocketProvider** is backed by a long-lived connection over a
 *  socket, which can subscribe and receive real-time messages over
 *  its communication channel.
 */
export declare class SocketProvider extends JsonRpcApiProvider {
    #private;
    /**
     *  Creates a new **SocketProvider** connected to %%network%%.
     *
     *  If unspecified, the network will be discovered.
     */
    constructor(network?: Networkish, _options?: JsonRpcApiProviderOptions);
    _getSubscriber(sub: Subscription): Subscriber;
    /**
     *  Register a new subscriber. This is used internalled by Subscribers
     *  and generally is unecessary unless extending capabilities.
     */
    _register(filterId: number | string, subscriber: SocketSubscriber): void;
    _send(payload: JsonRpcPayload | Array<JsonRpcPayload>): Promise<Array<JsonRpcResult | JsonRpcError>>;
    /**
     *  Sub-classes **must** call this with messages received over their
     *  transport to be processed and dispatched.
     */
    _processMessage(message: string): Promise<void>;
    /**
     *  Sub-classes **must** override this to send %%message%% over their
     *  transport.
     */
    _write(message: string): Promise<void>;
}
//# sourceMappingURL=provider-socket.d.ts.map