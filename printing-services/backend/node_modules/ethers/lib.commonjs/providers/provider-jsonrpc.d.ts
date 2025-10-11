/**
 *  One of the most common ways to interact with the blockchain is
 *  by a node running a JSON-RPC interface which can be connected to,
 *  based on the transport, using:
 *
 *  - HTTP or HTTPS - [[JsonRpcProvider]]
 *  - WebSocket - [[WebSocketProvider]]
 *  - IPC - [[IpcSocketProvider]]
 *
 * @_section: api/providers/jsonrpc:JSON-RPC Provider  [about-jsonrpcProvider]
 */
import { FetchRequest } from "../utils/index.js";
import { AbstractProvider } from "./abstract-provider.js";
import { AbstractSigner } from "./abstract-signer.js";
import { Network } from "./network.js";
import type { TypedDataDomain, TypedDataField } from "../hash/index.js";
import type { TransactionLike } from "../transaction/index.js";
import type { PerformActionRequest, Subscriber, Subscription } from "./abstract-provider.js";
import type { Networkish } from "./network.js";
import type { Provider, TransactionRequest, TransactionResponse } from "./provider.js";
import type { Signer } from "./signer.js";
/**
 *  A JSON-RPC payload, which are sent to a JSON-RPC server.
 */
export type JsonRpcPayload = {
    /**
     *  The JSON-RPC request ID.
     */
    id: number;
    /**
     *  The JSON-RPC request method.
     */
    method: string;
    /**
     *  The JSON-RPC request parameters.
     */
    params: Array<any> | Record<string, any>;
    /**
     *  A required constant in the JSON-RPC specification.
     */
    jsonrpc: "2.0";
};
/**
 *  A JSON-RPC result, which are returned on success from a JSON-RPC server.
 */
export type JsonRpcResult = {
    /**
     *  The response ID to match it to the relevant request.
     */
    id: number;
    /**
     *  The response result.
     */
    result: any;
};
/**
 *  A JSON-RPC error, which are returned on failure from a JSON-RPC server.
 */
export type JsonRpcError = {
    /**
     *  The response ID to match it to the relevant request.
     */
    id: number;
    /**
     *  The response error.
     */
    error: {
        code: number;
        message?: string;
        data?: any;
    };
};
/**
 *  When subscribing to the ``"debug"`` event, the [[Listener]] will
 *  receive this object as the first parameter.
 */
export type DebugEventJsonRpcApiProvider = {
    action: "sendRpcPayload";
    payload: JsonRpcPayload | Array<JsonRpcPayload>;
} | {
    action: "receiveRpcResult";
    result: Array<JsonRpcResult | JsonRpcError>;
} | {
    action: "receiveRpcError";
    error: Error;
};
/**
 *  Options for configuring a [[JsonRpcApiProvider]]. Much of this
 *  is targetted towards sub-classes, which often will not expose
 *  any of these options to their consumers.
 *
 *  **``polling``** - use the polling strategy is used immediately
 *  for events; otherwise, attempt to use filters and fall back onto
 *  polling (default: ``false``)
 *
 *  **``staticNetwork``** - do not request chain ID on requests to
 *  validate the underlying chain has not changed (default: ``null``)
 *
 *  This should **ONLY** be used if it is **certain** that the network
 *  cannot change, such as when using INFURA (since the URL dictates the
 *  network). If the network is assumed static and it does change, this
 *  can have tragic consequences. For example, this **CANNOT** be used
 *  with MetaMask, since the user can select a new network from the
 *  drop-down at any time.
 *
 *  **``batchStallTime``** - how long (ms) to aggregate requests into a
 *  single batch. ``0`` indicates batching will only encompass the current
 *  event loop. If ``batchMaxCount = 1``, this is ignored. (default: ``10``)
 *
 *  **``batchMaxSize``** - target maximum size (bytes) to allow per batch
 *  request (default: 1Mb)
 *
 *  **``batchMaxCount``** - maximum number of requests to allow in a batch.
 *  If ``batchMaxCount = 1``, then batching is disabled. (default: ``100``)
 *
 *  **``cacheTimeout``** - passed as [[AbstractProviderOptions]].
 */
export type JsonRpcApiProviderOptions = {
    polling?: boolean;
    staticNetwork?: null | boolean | Network;
    batchStallTime?: number;
    batchMaxSize?: number;
    batchMaxCount?: number;
    cacheTimeout?: number;
    pollingInterval?: number;
};
/**
 *  A **JsonRpcTransactionRequest** is formatted as needed by the JSON-RPC
 *  Ethereum API specification.
 */
export interface JsonRpcTransactionRequest {
    /**
     *  The sender address to use when signing.
     */
    from?: string;
    /**
     *  The target address.
     */
    to?: string;
    /**
     *  The transaction data.
     */
    data?: string;
    /**
     *  The chain ID the transaction is valid on.
     */
    chainId?: string;
    /**
     *  The [[link-eip-2718]] transaction type.
     */
    type?: string;
    /**
     *  The maximum amount of gas to allow a transaction to consume.
     *
     *  In most other places in ethers, this is called ``gasLimit`` which
     *  differs from the JSON-RPC Ethereum API specification.
     */
    gas?: string;
    /**
     *  The gas price per wei for transactions prior to [[link-eip-1559]].
     */
    gasPrice?: string;
    /**
     *  The maximum fee per gas for [[link-eip-1559]] transactions.
     */
    maxFeePerGas?: string;
    /**
     *  The maximum priority fee per gas for [[link-eip-1559]] transactions.
     */
    maxPriorityFeePerGas?: string;
    /**
     *  The nonce for the transaction.
     */
    nonce?: string;
    /**
     *  The transaction value (in wei).
     */
    value?: string;
    /**
     *  The transaction access list.
     */
    accessList?: Array<{
        address: string;
        storageKeys: Array<string>;
    }>;
    /**
     *  The transaction authorization list.
     */
    authorizationList?: Array<{
        address: string;
        nonce: string;
        chainId: string;
        yParity: string;
        r: string;
        s: string;
    }>;
}
export declare class JsonRpcSigner extends AbstractSigner<JsonRpcApiProvider> {
    address: string;
    constructor(provider: JsonRpcApiProvider, address: string);
    connect(provider: null | Provider): Signer;
    getAddress(): Promise<string>;
    populateTransaction(tx: TransactionRequest): Promise<TransactionLike<string>>;
    sendUncheckedTransaction(_tx: TransactionRequest): Promise<string>;
    sendTransaction(tx: TransactionRequest): Promise<TransactionResponse>;
    signTransaction(_tx: TransactionRequest): Promise<string>;
    signMessage(_message: string | Uint8Array): Promise<string>;
    signTypedData(domain: TypedDataDomain, types: Record<string, Array<TypedDataField>>, _value: Record<string, any>): Promise<string>;
    unlock(password: string): Promise<boolean>;
    _legacySignMessage(_message: string | Uint8Array): Promise<string>;
}
/**
 *  The JsonRpcApiProvider is an abstract class and **MUST** be
 *  sub-classed.
 *
 *  It provides the base for all JSON-RPC-based Provider interaction.
 *
 *  Sub-classing Notes:
 *  - a sub-class MUST override _send
 *  - a sub-class MUST call the `_start()` method once connected
 */
export declare abstract class JsonRpcApiProvider extends AbstractProvider {
    #private;
    constructor(network?: Networkish, options?: JsonRpcApiProviderOptions);
    /**
     *  Returns the value associated with the option %%key%%.
     *
     *  Sub-classes can use this to inquire about configuration options.
     */
    _getOption<K extends keyof JsonRpcApiProviderOptions>(key: K): JsonRpcApiProviderOptions[K];
    /**
     *  Gets the [[Network]] this provider has committed to. On each call, the network
     *  is detected, and if it has changed, the call will reject.
     */
    get _network(): Network;
    /**
     *  Sends a JSON-RPC %%payload%% (or a batch) to the underlying channel.
     *
     *  Sub-classes **MUST** override this.
     */
    abstract _send(payload: JsonRpcPayload | Array<JsonRpcPayload>): Promise<Array<JsonRpcResult | JsonRpcError>>;
    /**
     *  Resolves to the non-normalized value by performing %%req%%.
     *
     *  Sub-classes may override this to modify behavior of actions,
     *  and should generally call ``super._perform`` as a fallback.
     */
    _perform(req: PerformActionRequest): Promise<any>;
    /**
     *  Sub-classes may override this; it detects the *actual* network that
     *  we are **currently** connected to.
     *
     *  Keep in mind that [[send]] may only be used once [[ready]], otherwise the
     *  _send primitive must be used instead.
     */
    _detectNetwork(): Promise<Network>;
    /**
     *  Sub-classes **MUST** call this. Until [[_start]] has been called, no calls
     *  will be passed to [[_send]] from [[send]]. If it is overridden, then
     *  ``super._start()`` **MUST** be called.
     *
     *  Calling it multiple times is safe and has no effect.
     */
    _start(): void;
    /**
     *  Resolves once the [[_start]] has been called. This can be used in
     *  sub-classes to defer sending data until the connection has been
     *  established.
     */
    _waitUntilReady(): Promise<void>;
    /**
     *  Return a Subscriber that will manage the %%sub%%.
     *
     *  Sub-classes may override this to modify the behavior of
     *  subscription management.
     */
    _getSubscriber(sub: Subscription): Subscriber;
    /**
     *  Returns true only if the [[_start]] has been called.
     */
    get ready(): boolean;
    /**
     *  Returns %%tx%% as a normalized JSON-RPC transaction request,
     *  which has all values hexlified and any numeric values converted
     *  to Quantity values.
     */
    getRpcTransaction(tx: TransactionRequest): JsonRpcTransactionRequest;
    /**
     *  Returns the request method and arguments required to perform
     *  %%req%%.
     */
    getRpcRequest(req: PerformActionRequest): null | {
        method: string;
        args: Array<any>;
    };
    /**
     *  Returns an ethers-style Error for the given JSON-RPC error
     *  %%payload%%, coalescing the various strings and error shapes
     *  that different nodes return, coercing them into a machine-readable
     *  standardized error.
     */
    getRpcError(payload: JsonRpcPayload, _error: JsonRpcError): Error;
    /**
     *  Requests the %%method%% with %%params%% via the JSON-RPC protocol
     *  over the underlying channel. This can be used to call methods
     *  on the backend that do not have a high-level API within the Provider
     *  API.
     *
     *  This method queues requests according to the batch constraints
     *  in the options, assigns the request a unique ID.
     *
     *  **Do NOT override** this method in sub-classes; instead
     *  override [[_send]] or force the options values in the
     *  call to the constructor to modify this method's behavior.
     */
    send(method: string, params: Array<any> | Record<string, any>): Promise<any>;
    /**
     *  Resolves to the [[Signer]] account for  %%address%% managed by
     *  the client.
     *
     *  If the %%address%% is a number, it is used as an index in the
     *  the accounts from [[listAccounts]].
     *
     *  This can only be used on clients which manage accounts (such as
     *  Geth with imported account or MetaMask).
     *
     *  Throws if the account doesn't exist.
     */
    getSigner(address?: number | string): Promise<JsonRpcSigner>;
    listAccounts(): Promise<Array<JsonRpcSigner>>;
    destroy(): void;
}
/**
 *  @_ignore:
 */
export declare abstract class JsonRpcApiPollingProvider extends JsonRpcApiProvider {
    #private;
    constructor(network?: Networkish, options?: JsonRpcApiProviderOptions);
    _getSubscriber(sub: Subscription): Subscriber;
    /**
     *  The polling interval (default: 4000 ms)
     */
    get pollingInterval(): number;
    set pollingInterval(value: number);
}
/**
 *  The JsonRpcProvider is one of the most common Providers,
 *  which performs all operations over HTTP (or HTTPS) requests.
 *
 *  Events are processed by polling the backend for the current block
 *  number; when it advances, all block-base events are then checked
 *  for updates.
 */
export declare class JsonRpcProvider extends JsonRpcApiPollingProvider {
    #private;
    constructor(url?: string | FetchRequest, network?: Networkish, options?: JsonRpcApiProviderOptions);
    _getConnection(): FetchRequest;
    send(method: string, params: Array<any> | Record<string, any>): Promise<any>;
    _send(payload: JsonRpcPayload | Array<JsonRpcPayload>): Promise<Array<JsonRpcResult>>;
}
//# sourceMappingURL=provider-jsonrpc.d.ts.map