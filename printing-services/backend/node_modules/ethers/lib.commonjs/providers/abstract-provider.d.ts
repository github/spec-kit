/**
 *  The available providers should suffice for most developers purposes,
 *  but the [[AbstractProvider]] class has many features which enable
 *  sub-classing it for specific purposes.
 *
 *  @_section: api/providers/abstract-provider: Subclassing Provider  [abstract-provider]
 */
import { FetchRequest } from "../utils/index.js";
import { EnsResolver } from "./ens-resolver.js";
import { Network } from "./network.js";
import { Block, FeeData, Log, TransactionReceipt, TransactionResponse } from "./provider.js";
import type { AddressLike } from "../address/index.js";
import type { BigNumberish } from "../utils/index.js";
import type { Listener } from "../utils/index.js";
import type { Networkish } from "./network.js";
import type { BlockParams, LogParams, TransactionReceiptParams, TransactionResponseParams } from "./formatting.js";
import type { BlockTag, EventFilter, Filter, FilterByBlockHash, OrphanFilter, PreparedTransactionRequest, Provider, ProviderEvent, TransactionRequest } from "./provider.js";
/**
 *  The types of additional event values that can be emitted for the
 *  ``"debug"`` event.
 */
export type DebugEventAbstractProvider = {
    action: "sendCcipReadFetchRequest";
    request: FetchRequest;
    index: number;
    urls: Array<string>;
} | {
    action: "receiveCcipReadFetchResult";
    request: FetchRequest;
    result: any;
} | {
    action: "receiveCcipReadFetchError";
    request: FetchRequest;
    result: any;
} | {
    action: "sendCcipReadCall";
    transaction: {
        to: string;
        data: string;
    };
} | {
    action: "receiveCcipReadCallResult";
    transaction: {
        to: string;
        data: string;
    };
    result: string;
} | {
    action: "receiveCcipReadCallError";
    transaction: {
        to: string;
        data: string;
    };
    error: Error;
};
/**
 *  The value passed to the [[AbstractProvider-_getSubscriber]] method.
 *
 *  Only developers sub-classing [[AbstractProvider[[ will care about this,
 *  if they are modifying a low-level feature of how subscriptions operate.
 */
export type Subscription = {
    type: "block" | "close" | "debug" | "error" | "finalized" | "network" | "pending" | "safe";
    tag: string;
} | {
    type: "transaction";
    tag: string;
    hash: string;
} | {
    type: "event";
    tag: string;
    filter: EventFilter;
} | {
    type: "orphan";
    tag: string;
    filter: OrphanFilter;
};
/**
 *  A **Subscriber** manages a subscription.
 *
 *  Only developers sub-classing [[AbstractProvider[[ will care about this,
 *  if they are modifying a low-level feature of how subscriptions operate.
 */
export interface Subscriber {
    /**
     *  Called initially when a subscriber is added the first time.
     */
    start(): void;
    /**
     *  Called when there are no more subscribers to the event.
     */
    stop(): void;
    /**
     *  Called when the subscription should pause.
     *
     *  If %%dropWhilePaused%%, events that occur while paused should not
     *  be emitted [[resume]].
     */
    pause(dropWhilePaused?: boolean): void;
    /**
     *  Resume a paused subscriber.
     */
    resume(): void;
    /**
     *  The frequency (in ms) to poll for events, if polling is used by
     *  the subscriber.
     *
     *  For non-polling subscribers, this must return ``undefined``.
     */
    pollingInterval?: number;
}
/**
 *  An **UnmanagedSubscriber** is useful for events which do not require
 *  any additional management, such as ``"debug"`` which only requires
 *  emit in synchronous event loop triggered calls.
 */
export declare class UnmanagedSubscriber implements Subscriber {
    /**
     *  The name fof the event.
     */
    name: string;
    /**
     *  Create a new UnmanagedSubscriber with %%name%%.
     */
    constructor(name: string);
    start(): void;
    stop(): void;
    pause(dropWhilePaused?: boolean): void;
    resume(): void;
}
/**
 *  An **AbstractPlugin** is used to provide additional internal services
 *  to an [[AbstractProvider]] without adding backwards-incompatible changes
 *  to method signatures or other internal and complex logic.
 */
export interface AbstractProviderPlugin {
    /**
     *  The reverse domain notation of the plugin.
     */
    readonly name: string;
    /**
     *  Creates a new instance of the plugin, connected to %%provider%%.
     */
    connect(provider: AbstractProvider): AbstractProviderPlugin;
}
/**
 *  A normalized filter used for [[PerformActionRequest]] objects.
 */
export type PerformActionFilter = {
    address?: string | Array<string>;
    topics?: Array<null | string | Array<string>>;
    fromBlock?: BlockTag;
    toBlock?: BlockTag;
} | {
    address?: string | Array<string>;
    topics?: Array<null | string | Array<string>>;
    blockHash?: string;
};
/**
 *  A normalized transactions used for [[PerformActionRequest]] objects.
 */
export interface PerformActionTransaction extends PreparedTransactionRequest {
    /**
     *  The ``to`` address of the transaction.
     */
    to?: string;
    /**
     *  The sender of the transaction.
     */
    from?: string;
}
/**
 *  The [[AbstractProvider]] methods will normalize all values and pass this
 *  type to [[AbstractProvider-_perform]].
 */
export type PerformActionRequest = {
    method: "broadcastTransaction";
    signedTransaction: string;
} | {
    method: "call";
    transaction: PerformActionTransaction;
    blockTag: BlockTag;
} | {
    method: "chainId";
} | {
    method: "estimateGas";
    transaction: PerformActionTransaction;
} | {
    method: "getBalance";
    address: string;
    blockTag: BlockTag;
} | {
    method: "getBlock";
    blockTag: BlockTag;
    includeTransactions: boolean;
} | {
    method: "getBlock";
    blockHash: string;
    includeTransactions: boolean;
} | {
    method: "getBlockNumber";
} | {
    method: "getCode";
    address: string;
    blockTag: BlockTag;
} | {
    method: "getGasPrice";
} | {
    method: "getLogs";
    filter: PerformActionFilter;
} | {
    method: "getPriorityFee";
} | {
    method: "getStorage";
    address: string;
    position: bigint;
    blockTag: BlockTag;
} | {
    method: "getTransaction";
    hash: string;
} | {
    method: "getTransactionCount";
    address: string;
    blockTag: BlockTag;
} | {
    method: "getTransactionReceipt";
    hash: string;
} | {
    method: "getTransactionResult";
    hash: string;
};
/**
 *  Options for configuring some internal aspects of an [[AbstractProvider]].
 *
 *  **``cacheTimeout``** - how long to cache a low-level ``_perform``
 *  for, based on input parameters. This reduces the number of calls
 *  to getChainId and getBlockNumber, but may break test chains which
 *  can perform operations (internally) synchronously. Use ``-1`` to
 *  disable, ``0`` will only buffer within the same event loop and
 *  any other value is in ms. (default: ``250``)
 */
export type AbstractProviderOptions = {
    cacheTimeout?: number;
    pollingInterval?: number;
};
/**
 *  An **AbstractProvider** provides a base class for other sub-classes to
 *  implement the [[Provider]] API by normalizing input arguments and
 *  formatting output results as well as tracking events for consistent
 *  behaviour on an eventually-consistent network.
 */
export declare class AbstractProvider implements Provider {
    #private;
    /**
     *  Create a new **AbstractProvider** connected to %%network%%, or
     *  use the various network detection capabilities to discover the
     *  [[Network]] if necessary.
     */
    constructor(_network?: "any" | Networkish, options?: AbstractProviderOptions);
    get pollingInterval(): number;
    /**
     *  Returns ``this``, to allow an **AbstractProvider** to implement
     *  the [[ContractRunner]] interface.
     */
    get provider(): this;
    /**
     *  Returns all the registered plug-ins.
     */
    get plugins(): Array<AbstractProviderPlugin>;
    /**
     *  Attach a new plug-in.
     */
    attachPlugin(plugin: AbstractProviderPlugin): this;
    /**
     *  Get a plugin by name.
     */
    getPlugin<T extends AbstractProviderPlugin = AbstractProviderPlugin>(name: string): null | T;
    /**
     *  Prevent any CCIP-read operation, regardless of whether requested
     *  in a [[call]] using ``enableCcipRead``.
     */
    get disableCcipRead(): boolean;
    set disableCcipRead(value: boolean);
    /**
     *  Resolves to the data for executing the CCIP-read operations.
     */
    ccipReadFetch(tx: PerformActionTransaction, calldata: string, urls: Array<string>): Promise<null | string>;
    /**
     *  Provides the opportunity for a sub-class to wrap a block before
     *  returning it, to add additional properties or an alternate
     *  sub-class of [[Block]].
     */
    _wrapBlock(value: BlockParams, network: Network): Block;
    /**
     *  Provides the opportunity for a sub-class to wrap a log before
     *  returning it, to add additional properties or an alternate
     *  sub-class of [[Log]].
     */
    _wrapLog(value: LogParams, network: Network): Log;
    /**
     *  Provides the opportunity for a sub-class to wrap a transaction
     *  receipt before returning it, to add additional properties or an
     *  alternate sub-class of [[TransactionReceipt]].
     */
    _wrapTransactionReceipt(value: TransactionReceiptParams, network: Network): TransactionReceipt;
    /**
     *  Provides the opportunity for a sub-class to wrap a transaction
     *  response before returning it, to add additional properties or an
     *  alternate sub-class of [[TransactionResponse]].
     */
    _wrapTransactionResponse(tx: TransactionResponseParams, network: Network): TransactionResponse;
    /**
     *  Resolves to the Network, forcing a network detection using whatever
     *  technique the sub-class requires.
     *
     *  Sub-classes **must** override this.
     */
    _detectNetwork(): Promise<Network>;
    /**
     *  Sub-classes should use this to perform all built-in operations. All
     *  methods sanitizes and normalizes the values passed into this.
     *
     *  Sub-classes **must** override this.
     */
    _perform<T = any>(req: PerformActionRequest): Promise<T>;
    getBlockNumber(): Promise<number>;
    /**
     *  Returns or resolves to the address for %%address%%, resolving ENS
     *  names and [[Addressable]] objects and returning if already an
     *  address.
     */
    _getAddress(address: AddressLike): string | Promise<string>;
    /**
     *  Returns or resolves to a valid block tag for %%blockTag%%, resolving
     *  negative values and returning if already a valid block tag.
     */
    _getBlockTag(blockTag?: BlockTag): string | Promise<string>;
    /**
     *  Returns or resolves to a filter for %%filter%%, resolving any ENS
     *  names or [[Addressable]] object and returning if already a valid
     *  filter.
     */
    _getFilter(filter: Filter | FilterByBlockHash): PerformActionFilter | Promise<PerformActionFilter>;
    /**
     *  Returns or resolves to a transaction for %%request%%, resolving
     *  any ENS names or [[Addressable]] and returning if already a valid
     *  transaction.
     */
    _getTransactionRequest(_request: TransactionRequest): PerformActionTransaction | Promise<PerformActionTransaction>;
    getNetwork(): Promise<Network>;
    getFeeData(): Promise<FeeData>;
    estimateGas(_tx: TransactionRequest): Promise<bigint>;
    call(_tx: TransactionRequest): Promise<string>;
    getBalance(address: AddressLike, blockTag?: BlockTag): Promise<bigint>;
    getTransactionCount(address: AddressLike, blockTag?: BlockTag): Promise<number>;
    getCode(address: AddressLike, blockTag?: BlockTag): Promise<string>;
    getStorage(address: AddressLike, _position: BigNumberish, blockTag?: BlockTag): Promise<string>;
    broadcastTransaction(signedTx: string): Promise<TransactionResponse>;
    getBlock(block: BlockTag | string, prefetchTxs?: boolean): Promise<null | Block>;
    getTransaction(hash: string): Promise<null | TransactionResponse>;
    getTransactionReceipt(hash: string): Promise<null | TransactionReceipt>;
    getTransactionResult(hash: string): Promise<null | string>;
    getLogs(_filter: Filter | FilterByBlockHash): Promise<Array<Log>>;
    _getProvider(chainId: number): AbstractProvider;
    getResolver(name: string): Promise<null | EnsResolver>;
    getAvatar(name: string): Promise<null | string>;
    resolveName(name: string): Promise<null | string>;
    lookupAddress(address: string): Promise<null | string>;
    waitForTransaction(hash: string, _confirms?: null | number, timeout?: null | number): Promise<null | TransactionReceipt>;
    waitForBlock(blockTag?: BlockTag): Promise<Block>;
    /**
     *  Clear a timer created using the [[_setTimeout]] method.
     */
    _clearTimeout(timerId: number): void;
    /**
     *  Create a timer that will execute %%func%% after at least %%timeout%%
     *  (in ms). If %%timeout%% is unspecified, then %%func%% will execute
     *  in the next event loop.
     *
     *  [Pausing](AbstractProvider-paused) the provider will pause any
     *  associated timers.
     */
    _setTimeout(_func: () => void, timeout?: number): number;
    /**
     *  Perform %%func%% on each subscriber.
     */
    _forEachSubscriber(func: (s: Subscriber) => void): void;
    /**
     *  Sub-classes may override this to customize subscription
     *  implementations.
     */
    _getSubscriber(sub: Subscription): Subscriber;
    /**
     *  If a [[Subscriber]] fails and needs to replace itself, this
     *  method may be used.
     *
     *  For example, this is used for providers when using the
     *  ``eth_getFilterChanges`` method, which can return null if state
     *  filters are not supported by the backend, allowing the Subscriber
     *  to swap in a [[PollingEventSubscriber]].
     */
    _recoverSubscriber(oldSub: Subscriber, newSub: Subscriber): void;
    on(event: ProviderEvent, listener: Listener): Promise<this>;
    once(event: ProviderEvent, listener: Listener): Promise<this>;
    emit(event: ProviderEvent, ...args: Array<any>): Promise<boolean>;
    listenerCount(event?: ProviderEvent): Promise<number>;
    listeners(event?: ProviderEvent): Promise<Array<Listener>>;
    off(event: ProviderEvent, listener?: Listener): Promise<this>;
    removeAllListeners(event?: ProviderEvent): Promise<this>;
    addListener(event: ProviderEvent, listener: Listener): Promise<this>;
    removeListener(event: ProviderEvent, listener: Listener): Promise<this>;
    /**
     *  If this provider has been destroyed using the [[destroy]] method.
     *
     *  Once destroyed, all resources are reclaimed, internal event loops
     *  and timers are cleaned up and no further requests may be sent to
     *  the provider.
     */
    get destroyed(): boolean;
    /**
     *  Sub-classes may use this to shutdown any sockets or release their
     *  resources and reject any pending requests.
     *
     *  Sub-classes **must** call ``super.destroy()``.
     */
    destroy(): void;
    /**
     *  Whether the provider is currently paused.
     *
     *  A paused provider will not emit any events, and generally should
     *  not make any requests to the network, but that is up to sub-classes
     *  to manage.
     *
     *  Setting ``paused = true`` is identical to calling ``.pause(false)``,
     *  which will buffer any events that occur while paused until the
     *  provider is unpaused.
     */
    get paused(): boolean;
    set paused(pause: boolean);
    /**
     *  Pause the provider. If %%dropWhilePaused%%, any events that occur
     *  while paused are dropped, otherwise all events will be emitted once
     *  the provider is unpaused.
     */
    pause(dropWhilePaused?: boolean): void;
    /**
     *  Resume the provider.
     */
    resume(): void;
}
//# sourceMappingURL=abstract-provider.d.ts.map