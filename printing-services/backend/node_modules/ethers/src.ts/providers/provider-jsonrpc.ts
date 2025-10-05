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

// @TODO:
// - Add the batching API

// https://playground.open-rpc.org/?schemaUrl=https://raw.githubusercontent.com/ethereum/eth1.0-apis/assembled-spec/openrpc.json&uiSchema%5BappBar%5D%5Bui:splitView%5D=true&uiSchema%5BappBar%5D%5Bui:input%5D=false&uiSchema%5BappBar%5D%5Bui:examplesDropdown%5D=false

import { AbiCoder } from "../abi/index.js";
import { getAddress, resolveAddress } from "../address/index.js";
import { TypedDataEncoder } from "../hash/index.js";
import { accessListify, authorizationify } from "../transaction/index.js";
import {
    defineProperties, getBigInt, hexlify, isHexString, toQuantity, toUtf8Bytes,
    isError, makeError, assert, assertArgument,
    FetchRequest, resolveProperties
} from "../utils/index.js";

import { AbstractProvider, UnmanagedSubscriber } from "./abstract-provider.js";
import { AbstractSigner } from "./abstract-signer.js";
import { Network } from "./network.js";
import { FilterIdEventSubscriber, FilterIdPendingSubscriber } from "./subscriber-filterid.js";
import { PollingEventSubscriber } from "./subscriber-polling.js";

import type { TypedDataDomain, TypedDataField } from "../hash/index.js";
import type { TransactionLike } from "../transaction/index.js";

import type { PerformActionRequest, Subscriber, Subscription } from "./abstract-provider.js";
import type { Networkish } from "./network.js";
import type { Provider, TransactionRequest, TransactionResponse } from "./provider.js";
import type { Signer } from "./signer.js";

type Timer = ReturnType<typeof setTimeout>;

const Primitive = "bigint,boolean,function,number,string,symbol".split(/,/g);
//const Methods = "getAddress,then".split(/,/g);
function deepCopy<T = any>(value: T): T {
    if (value == null || Primitive.indexOf(typeof(value)) >= 0) {
        return value;
    }

    // Keep any Addressable
    if (typeof((<any>value).getAddress) === "function") {
        return value;
    }

    if (Array.isArray(value)) { return <any>(value.map(deepCopy)); }

    if (typeof(value) === "object") {
        return Object.keys(value).reduce((accum, key) => {
            accum[key] = (<any>value)[key];
            return accum;
        }, <any>{ });
    }

    throw new Error(`should not happen: ${ value } (${ typeof(value) })`);
}

function stall(duration: number): Promise<void> {
    return new Promise((resolve) => { setTimeout(resolve, duration); });
}

function getLowerCase(value: string): string {
    if (value) { return value.toLowerCase(); }
    return value;
}

interface Pollable {
    pollingInterval: number;
}

function isPollable(value: any): value is Pollable {
    return (value && typeof(value.pollingInterval) === "number");
}

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
    }
};

/**
 *  When subscribing to the ``"debug"`` event, the [[Listener]] will
 *  receive this object as the first parameter.
 */
export type DebugEventJsonRpcApiProvider = {
    action: "sendRpcPayload",
    payload: JsonRpcPayload | Array<JsonRpcPayload>
} | {
    action: "receiveRpcResult",
    result: Array<JsonRpcResult | JsonRpcError>
} | {
    action: "receiveRpcError",
    error: Error
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

const defaultOptions = {
    polling: false,
    staticNetwork: null,

    batchStallTime: 10,      // 10ms
    batchMaxSize: (1 << 20), // 1Mb
    batchMaxCount: 100,      // 100 requests

    cacheTimeout: 250,
    pollingInterval: 4000
}

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
     accessList?: Array<{ address: string, storageKeys: Array<string> }>;

     /**
      *  The transaction authorization list.
      */
     authorizationList?: Array<{
         address: string, nonce: string, chainId: string,
         yParity: string, r: string, s: string
     }>;
}

// @TODO: Unchecked Signers

export class JsonRpcSigner extends AbstractSigner<JsonRpcApiProvider> {
    address!: string;

    constructor(provider: JsonRpcApiProvider, address: string) {
        super(provider);
        address = getAddress(address);
        defineProperties<JsonRpcSigner>(this, { address });
    }

    connect(provider: null | Provider): Signer {
        assert(false, "cannot reconnect JsonRpcSigner", "UNSUPPORTED_OPERATION", {
            operation: "signer.connect"
        });
    }

    async getAddress(): Promise<string> {
        return this.address;
    }

    // JSON-RPC will automatially fill in nonce, etc. so we just check from
    async populateTransaction(tx: TransactionRequest): Promise<TransactionLike<string>> {
        return await this.populateCall(tx);
    }

    // Returns just the hash of the transaction after sent, which is what
    // the bare JSON-RPC API does;
    async sendUncheckedTransaction(_tx: TransactionRequest): Promise<string> {
        const tx = deepCopy(_tx);

        const promises: Array<Promise<void>> = [];

        // Make sure the from matches the sender
        if (tx.from) {
            const _from = tx.from;
            promises.push((async () => {
                const from = await resolveAddress(_from, this.provider);
                assertArgument(from != null && from.toLowerCase() === this.address.toLowerCase(),
                    "from address mismatch", "transaction", _tx);
                tx.from = from;
            })());
        } else {
            tx.from = this.address;
        }

        // The JSON-RPC for eth_sendTransaction uses 90000 gas; if the user
        // wishes to use this, it is easy to specify explicitly, otherwise
        // we look it up for them.
        if (tx.gasLimit == null) {
            promises.push((async () => {
                tx.gasLimit = await this.provider.estimateGas({ ...tx, from: this.address});
            })());
        }

        // The address may be an ENS name or Addressable
        if (tx.to != null) {
            const _to = tx.to;
            promises.push((async () => {
                tx.to = await resolveAddress(_to, this.provider);
            })());
        }

        // Wait until all of our properties are filled in
        if (promises.length) { await Promise.all(promises); }

        const hexTx = this.provider.getRpcTransaction(tx);

        return this.provider.send("eth_sendTransaction", [ hexTx ]);
    }

    async sendTransaction(tx: TransactionRequest): Promise<TransactionResponse> {
        // This cannot be mined any earlier than any recent block
        const blockNumber = await this.provider.getBlockNumber();

        // Send the transaction
        const hash = await this.sendUncheckedTransaction(tx);

        // Unfortunately, JSON-RPC only provides and opaque transaction hash
        // for a response, and we need the actual transaction, so we poll
        // for it; it should show up very quickly
        return await (new Promise((resolve, reject) => {
            const timeouts = [ 1000, 100 ];
            let invalids = 0;

            const checkTx = async () => {

                try {
                    // Try getting the transaction
                    const tx = await this.provider.getTransaction(hash);

                    if (tx != null) {
                        resolve(tx.replaceableTransaction(blockNumber));
                        return;
                    }

                } catch (error) {

                    // If we were cancelled: stop polling.
                    // If the data is bad: the node returns bad transactions
                    // If the network changed: calling again will also fail
                    // If unsupported: likely destroyed
                    if (isError(error, "CANCELLED") || isError(error, "BAD_DATA") ||
                        isError(error, "NETWORK_ERROR") || isError(error, "UNSUPPORTED_OPERATION")) {

                        if (error.info == null) { error.info = { }; }
                        error.info.sendTransactionHash = hash;

                        reject(error);
                        return;
                    }

                    // Stop-gap for misbehaving backends; see #4513
                    if (isError(error, "INVALID_ARGUMENT")) {
                        invalids++;
                        if (error.info == null) { error.info = { }; }
                        error.info.sendTransactionHash = hash;
                        if (invalids > 10) {
                            reject(error);
                            return;
                        }
                    }

                    // Notify anyone that cares; but we will try again, since
                    // it is likely an intermittent service error
                    this.provider.emit("error", makeError("failed to fetch transation after sending (will try again)", "UNKNOWN_ERROR", { error }));
                }

                // Wait another 4 seconds
                this.provider._setTimeout(() => { checkTx(); }, timeouts.pop() || 4000);
            };
            checkTx();
        }));
    }

    async signTransaction(_tx: TransactionRequest): Promise<string> {
        const tx = deepCopy(_tx);

        // Make sure the from matches the sender
        if (tx.from) {
            const from = await resolveAddress(tx.from, this.provider);
            assertArgument(from != null && from.toLowerCase() === this.address.toLowerCase(),
                "from address mismatch", "transaction", _tx);
            tx.from = from;
        } else {
            tx.from = this.address;
        }

        const hexTx = this.provider.getRpcTransaction(tx);
        return await this.provider.send("eth_signTransaction", [ hexTx ]);
    }


    async signMessage(_message: string | Uint8Array): Promise<string> {
        const message = ((typeof(_message) === "string") ? toUtf8Bytes(_message): _message);
        return await this.provider.send("personal_sign", [
            hexlify(message), this.address.toLowerCase() ]);
    }

    async signTypedData(domain: TypedDataDomain, types: Record<string, Array<TypedDataField>>, _value: Record<string, any>): Promise<string> {
        const value = deepCopy(_value);

        // Populate any ENS names (in-place)
        const populated = await TypedDataEncoder.resolveNames(domain, types, value, async (value: string) => {
            const address = await resolveAddress(value);
            assertArgument(address != null, "TypedData does not support null address", "value", value);
            return address;
        });

        return await this.provider.send("eth_signTypedData_v4", [
            this.address.toLowerCase(),
            JSON.stringify(TypedDataEncoder.getPayload(populated.domain, types, populated.value))
        ]);
    }

    async unlock(password: string): Promise<boolean> {
        return this.provider.send("personal_unlockAccount", [
            this.address.toLowerCase(), password, null ]);
    }

    // https://github.com/ethereum/wiki/wiki/JSON-RPC#eth_sign
    async _legacySignMessage(_message: string | Uint8Array): Promise<string> {
        const message = ((typeof(_message) === "string") ? toUtf8Bytes(_message): _message);
        return await this.provider.send("eth_sign", [
            this.address.toLowerCase(), hexlify(message) ]);
    }
}

type ResolveFunc = (result: JsonRpcResult) => void;
type RejectFunc = (error: Error) => void;

type Payload = { payload: JsonRpcPayload, resolve: ResolveFunc, reject: RejectFunc };

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
export abstract class JsonRpcApiProvider extends AbstractProvider {

    #options: Required<JsonRpcApiProviderOptions>;

    // The next ID to use for the JSON-RPC ID field
    #nextId: number;

    // Payloads are queued and triggered in batches using the drainTimer
    #payloads: Array<Payload>;
    #drainTimer: null | Timer;

    #notReady: null | {
        promise: Promise<void>,
        resolve: null | ((v: void) => void)
    };

    #network: null | Network;
    #pendingDetectNetwork: null | Promise<Network>;

    #scheduleDrain(): void {
        if (this.#drainTimer) { return; }

        // If we aren't using batching, no harm in sending it immediately
        const stallTime = (this._getOption("batchMaxCount") === 1) ? 0: this._getOption("batchStallTime");

        this.#drainTimer = setTimeout(() => {
            this.#drainTimer = null;

            const payloads = this.#payloads;
            this.#payloads = [ ];

            while (payloads.length) {

                // Create payload batches that satisfy our batch constraints
                const batch = [ <Payload>(payloads.shift()) ];
                while (payloads.length) {
                    if (batch.length === this.#options.batchMaxCount) { break; }
                    batch.push(<Payload>(payloads.shift()));
                    const bytes = JSON.stringify(batch.map((p) => p.payload));
                    if (bytes.length > this.#options.batchMaxSize) {
                        payloads.unshift(<Payload>(batch.pop()));
                        break;
                    }
                }

                // Process the result to each payload
                (async () => {
                    const payload = ((batch.length === 1) ? batch[0].payload: batch.map((p) => p.payload));

                    this.emit("debug", { action: "sendRpcPayload", payload });

                    try {
                        const result = await this._send(payload);
                        this.emit("debug", { action: "receiveRpcResult", result });

                        // Process results in batch order
                        for (const { resolve, reject, payload } of batch) {

                            if (this.destroyed) {
                                reject(makeError("provider destroyed; cancelled request", "UNSUPPORTED_OPERATION", { operation: payload.method }));
                                continue;
                            }

                            // Find the matching result
                            const resp = result.filter((r) => (r.id === payload.id))[0];

                            // No result; the node failed us in unexpected ways
                            if (resp == null) {
                                const error = makeError("missing response for request", "BAD_DATA", {
                                    value: result, info: { payload }
                                });
                                this.emit("error", error);
                                reject(error);
                                continue;
                            }

                            // The response is an error
                            if ("error" in resp) {
                                reject(this.getRpcError(payload, resp));
                                continue;
                            }

                            // All good; send the result
                            resolve(resp.result);
                        }

                    } catch (error: any) {
                        this.emit("debug", { action: "receiveRpcError", error });

                        for (const { reject } of batch) {
                            // @TODO: augment the error with the payload
                            reject(error);
                        }
                    }
                })();
            }
        }, stallTime);
    }

    constructor(network?: Networkish, options?: JsonRpcApiProviderOptions) {
        super(network, options);

        this.#nextId = 1;
        this.#options = Object.assign({ }, defaultOptions, options || { });

        this.#payloads = [ ];
        this.#drainTimer = null;

        this.#network = null;
        this.#pendingDetectNetwork = null;

        {
            let resolve: null | ((value: void) => void) = null;
            const promise = new Promise((_resolve: (value: void) => void) => {
                resolve = _resolve;
            });
            this.#notReady = { promise, resolve };
        }

        const staticNetwork = this._getOption("staticNetwork");
        if (typeof(staticNetwork) === "boolean") {
            assertArgument(!staticNetwork || network !== "any", "staticNetwork cannot be used on special network 'any'", "options", options);
            if (staticNetwork && network != null) {
                this.#network = Network.from(network);
            }

        } else if (staticNetwork) {
            // Make sure any static network is compatbile with the provided netwrok
            assertArgument(network == null || staticNetwork.matches(network),
                "staticNetwork MUST match network object", "options", options);
            this.#network = staticNetwork;
        }
    }

    /**
     *  Returns the value associated with the option %%key%%.
     *
     *  Sub-classes can use this to inquire about configuration options.
     */
    _getOption<K extends keyof JsonRpcApiProviderOptions>(key: K): JsonRpcApiProviderOptions[K] {
        return this.#options[key];
    }

    /**
     *  Gets the [[Network]] this provider has committed to. On each call, the network
     *  is detected, and if it has changed, the call will reject.
     */
    get _network(): Network {
        assert (this.#network, "network is not available yet", "NETWORK_ERROR");
        return this.#network;
    }

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
    async _perform(req: PerformActionRequest): Promise<any> {

        // Legacy networks do not like the type field being passed along (which
        // is fair), so we delete type if it is 0 and a non-EIP-1559 network
        if (req.method === "call" || req.method === "estimateGas") {
            let tx = req.transaction;
            if (tx && tx.type != null && getBigInt(tx.type)) {
                // If there are no EIP-1559 or newer properties, it might be pre-EIP-1559
                if (tx.maxFeePerGas == null && tx.maxPriorityFeePerGas == null) {
                    const feeData = await this.getFeeData();
                    if (feeData.maxFeePerGas == null && feeData.maxPriorityFeePerGas == null) {
                        // Network doesn't know about EIP-1559 (and hence type)
                        req = Object.assign({ }, req, {
                            transaction: Object.assign({ }, tx, { type: undefined })
                        });
                    }
                }
            }
        }

        const request = this.getRpcRequest(req);

        if (request != null) {
            return await this.send(request.method, request.args);
        }

        return super._perform(req);
    }

    /**
     *  Sub-classes may override this; it detects the *actual* network that
     *  we are **currently** connected to.
     *
     *  Keep in mind that [[send]] may only be used once [[ready]], otherwise the
     *  _send primitive must be used instead.
     */
    async _detectNetwork(): Promise<Network> {
        const network = this._getOption("staticNetwork");
        if (network) {
            if (network === true) {
                if (this.#network) { return this.#network; }
            } else {
                return network;
            }
        }

        if (this.#pendingDetectNetwork) {
            return await this.#pendingDetectNetwork;
        }

        // If we are ready, use ``send``, which enabled requests to be batched
        if (this.ready) {
            this.#pendingDetectNetwork = (async () => {
                try {
                    const result = Network.from(getBigInt(await this.send("eth_chainId", [ ])));
                    this.#pendingDetectNetwork = null;
                    return result;
                } catch (error) {
                    this.#pendingDetectNetwork = null;
                    throw error;
                }
            })();
            return await this.#pendingDetectNetwork;
        }

        // We are not ready yet; use the primitive _send
        this.#pendingDetectNetwork = (async () => {
            const payload: JsonRpcPayload = {
                id: this.#nextId++, method: "eth_chainId", params: [ ], jsonrpc: "2.0"
            };

            this.emit("debug", { action: "sendRpcPayload", payload });

            let result: JsonRpcResult | JsonRpcError;
            try {
                result = (await this._send(payload))[0];
                this.#pendingDetectNetwork = null;
            } catch (error) {
                this.#pendingDetectNetwork = null;
                this.emit("debug", { action: "receiveRpcError", error });
                throw error;
            }

            this.emit("debug", { action: "receiveRpcResult", result });

            if ("result" in result) {
                return Network.from(getBigInt(result.result));
            }

            throw this.getRpcError(payload, result);
        })();

        return await this.#pendingDetectNetwork;
    }

    /**
     *  Sub-classes **MUST** call this. Until [[_start]] has been called, no calls
     *  will be passed to [[_send]] from [[send]]. If it is overridden, then
     *  ``super._start()`` **MUST** be called.
     *
     *  Calling it multiple times is safe and has no effect.
     */
    _start(): void {
        if (this.#notReady == null || this.#notReady.resolve == null) { return; }

        this.#notReady.resolve();
        this.#notReady = null;

        (async () => {

            // Bootstrap the network
            while (this.#network == null && !this.destroyed) {
                try {
                    this.#network = await this._detectNetwork();
                } catch (error) {
                    if (this.destroyed) { break; }
                    console.log("JsonRpcProvider failed to detect network and cannot start up; retry in 1s (perhaps the URL is wrong or the node is not started)");
                    this.emit("error", makeError("failed to bootstrap network detection", "NETWORK_ERROR", { event: "initial-network-discovery", info: { error } }));
                    await stall(1000);
                }
            }

            // Start dispatching requests
            this.#scheduleDrain();
        })();
    }

    /**
     *  Resolves once the [[_start]] has been called. This can be used in
     *  sub-classes to defer sending data until the connection has been
     *  established.
     */
    async _waitUntilReady(): Promise<void> {
        if (this.#notReady == null) { return; }
        return await this.#notReady.promise;
    }


    /**
     *  Return a Subscriber that will manage the %%sub%%.
     *
     *  Sub-classes may override this to modify the behavior of
     *  subscription management.
     */
    _getSubscriber(sub: Subscription): Subscriber {

        // Pending Filters aren't availble via polling
        if (sub.type === "pending") { return new FilterIdPendingSubscriber(this); }

        if (sub.type === "event") {
            if (this._getOption("polling")) {
                return new PollingEventSubscriber(this, sub.filter);
            }
            return new FilterIdEventSubscriber(this, sub.filter);
        }

        // Orphaned Logs are handled automatically, by the filter, since
        // logs with removed are emitted by it
        if (sub.type === "orphan" && sub.filter.orphan === "drop-log") {
            return new UnmanagedSubscriber("orphan");
        }

        return super._getSubscriber(sub);
    }

    /**
     *  Returns true only if the [[_start]] has been called.
     */
    get ready(): boolean { return this.#notReady == null; }

    /**
     *  Returns %%tx%% as a normalized JSON-RPC transaction request,
     *  which has all values hexlified and any numeric values converted
     *  to Quantity values.
     */
    getRpcTransaction(tx: TransactionRequest): JsonRpcTransactionRequest {
        const result: JsonRpcTransactionRequest = {};

        // JSON-RPC now requires numeric values to be "quantity" values
        ["chainId", "gasLimit", "gasPrice", "type", "maxFeePerGas", "maxPriorityFeePerGas", "nonce", "value"].forEach((key) => {
            if ((<any>tx)[key] == null) { return; }
            let dstKey = key;
            if (key === "gasLimit") { dstKey = "gas"; }
            (<any>result)[dstKey] = toQuantity(getBigInt((<any>tx)[key], `tx.${ key }`));
        });

        // Make sure addresses and data are lowercase
        ["from", "to", "data"].forEach((key) => {
            if ((<any>tx)[key] == null) { return; }
            (<any>result)[key] = hexlify((<any>tx)[key]);
        });

        // Normalize the access list object
        if (tx.accessList) {
            result["accessList"] = accessListify(tx.accessList);
        }

        if (tx.blobVersionedHashes) {
            // @TODO: Remove this <any> case once EIP-4844 added to prepared tx
            (<any>result)["blobVersionedHashes"] = tx.blobVersionedHashes.map(h => h.toLowerCase());
        }

        if (tx.authorizationList) {
            result["authorizationList"] = tx.authorizationList.map((_a) => {
                const a = authorizationify(_a);
                return {
                    address: a.address,
                    nonce: toQuantity(a.nonce),
                    chainId: toQuantity(a.chainId),
                    yParity: toQuantity(a.signature.yParity),
                    r: toQuantity(a.signature.r),
                    s: toQuantity(a.signature.s),
                }
            });
        }

        // @TODO: blobs should probably also be copied over, optionally
        // accounting for the kzg property to backfill blobVersionedHashes
        // using the commitment. Or should that be left as an exercise to
        // the caller?

        return result;
    }

    /**
     *  Returns the request method and arguments required to perform
     *  %%req%%.
     */
    getRpcRequest(req: PerformActionRequest): null | { method: string, args: Array<any> } {
        switch (req.method) {
            case "chainId":
                return { method: "eth_chainId", args: [ ] };

            case "getBlockNumber":
                return { method: "eth_blockNumber", args: [ ] };

            case "getGasPrice":
                return { method: "eth_gasPrice", args: [] };

            case "getPriorityFee":
                return { method: "eth_maxPriorityFeePerGas", args: [ ] };

            case "getBalance":
                return {
                    method: "eth_getBalance",
                    args: [ getLowerCase(req.address), req.blockTag ]
                };

            case "getTransactionCount":
                return {
                    method: "eth_getTransactionCount",
                    args: [ getLowerCase(req.address), req.blockTag ]
                };

            case "getCode":
                return {
                    method: "eth_getCode",
                    args: [ getLowerCase(req.address), req.blockTag ]
                };

            case "getStorage":
                return {
                    method: "eth_getStorageAt",
                    args: [
                        getLowerCase(req.address),
                        ("0x" + req.position.toString(16)),
                        req.blockTag
                    ]
                };

            case "broadcastTransaction":
                return {
                    method: "eth_sendRawTransaction",
                    args: [ req.signedTransaction ]
                };

            case "getBlock":
                if ("blockTag" in req) {
                    return {
                        method: "eth_getBlockByNumber",
                        args: [ req.blockTag, !!req.includeTransactions ]
                    };
                } else if ("blockHash" in req) {
                    return {
                        method: "eth_getBlockByHash",
                        args: [ req.blockHash, !!req.includeTransactions ]
                    };
                }
                break;

            case "getTransaction":
                return {
                    method: "eth_getTransactionByHash",
                    args: [ req.hash ]
                };

            case "getTransactionReceipt":
                return {
                    method: "eth_getTransactionReceipt",
                    args: [ req.hash ]
                };

            case "call":
                return {
                    method: "eth_call",
                    args: [ this.getRpcTransaction(req.transaction), req.blockTag ]
                };

            case "estimateGas": {
                return {
                    method: "eth_estimateGas",
                    args: [ this.getRpcTransaction(req.transaction) ]
                };
            }

            case "getLogs":
                if (req.filter && req.filter.address != null) {
                    if (Array.isArray(req.filter.address)) {
                        req.filter.address = req.filter.address.map(getLowerCase);
                    } else {
                        req.filter.address = getLowerCase(req.filter.address);
                    }
                }
                return { method: "eth_getLogs", args: [ req.filter ] };
        }

        return null;
    }

    /**
     *  Returns an ethers-style Error for the given JSON-RPC error
     *  %%payload%%, coalescing the various strings and error shapes
     *  that different nodes return, coercing them into a machine-readable
     *  standardized error.
     */
    getRpcError(payload: JsonRpcPayload, _error: JsonRpcError): Error {
        const { method } = payload;
        const { error } = _error;

        if (method === "eth_estimateGas" && error.message) {
            const msg = error.message;
            if (!msg.match(/revert/i) && msg.match(/insufficient funds/i)) {
                return makeError("insufficient funds", "INSUFFICIENT_FUNDS", {
                    transaction: ((<any>payload).params[0]),
                    info: { payload, error }
                });
            } else if (msg.match(/nonce/i) && msg.match(/too low/i)) {
                return makeError("nonce has already been used", "NONCE_EXPIRED", {
                    transaction: ((<any>payload).params[0]),
                    info: { payload, error }
                });
            }
        }

        if (method === "eth_call" || method === "eth_estimateGas") {
            const result = spelunkData(error);

            const e = AbiCoder.getBuiltinCallException(
                (method === "eth_call") ? "call": "estimateGas",
                ((<any>payload).params[0]),
                (result ? result.data: null)
            );
            e.info = { error, payload };
            return e;
        }

        // Only estimateGas and call can return arbitrary contract-defined text, so now we
        // we can process text safely.

        const message = JSON.stringify(spelunkMessage(error));

        if (typeof(error.message) === "string" && error.message.match(/user denied|ethers-user-denied/i)) {
            const actionMap: Record<string, "requestAccess" | "sendTransaction" | "signMessage" | "signTransaction" | "signTypedData"> = {
                eth_sign: "signMessage",
                personal_sign: "signMessage",
                eth_signTypedData_v4: "signTypedData",
                eth_signTransaction: "signTransaction",
                eth_sendTransaction: "sendTransaction",
                eth_requestAccounts: "requestAccess",
                wallet_requestAccounts: "requestAccess",
            };

            return makeError(`user rejected action`, "ACTION_REJECTED", {
                action: (actionMap[method] || "unknown") ,
                reason: "rejected",
                info: { payload, error }
            });
        }

        if (method === "eth_sendRawTransaction" || method === "eth_sendTransaction") {
            const transaction = <TransactionLike<string>>((<any>payload).params[0]);

            if (message.match(/insufficient funds|base fee exceeds gas limit/i)) {
                return makeError("insufficient funds for intrinsic transaction cost", "INSUFFICIENT_FUNDS", {
                    transaction, info: { error }
                });
            }

            if (message.match(/nonce/i) && message.match(/too low/i)) {
                return makeError("nonce has already been used", "NONCE_EXPIRED", { transaction, info: { error } });
            }

            // "replacement transaction underpriced"
            if (message.match(/replacement transaction/i) && message.match(/underpriced/i)) {
                return makeError("replacement fee too low", "REPLACEMENT_UNDERPRICED", { transaction, info: { error } });
            }

            if (message.match(/only replay-protected/i)) {
                return makeError("legacy pre-eip-155 transactions not supported", "UNSUPPORTED_OPERATION", {
                    operation: method, info: { transaction, info: { error } }
                });
            }
        }

        let unsupported = !!message.match(/the method .* does not exist/i);
        if (!unsupported) {
            if (error && (<any>error).details && (<any>error).details.startsWith("Unauthorized method:")) {
                unsupported = true;
            }
        }

        if (unsupported) {
            return makeError("unsupported operation", "UNSUPPORTED_OPERATION", {
                operation: payload.method, info: { error, payload }
            });
        }

        return makeError("could not coalesce error", "UNKNOWN_ERROR", { error, payload });
    }


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
    send(method: string, params: Array<any> | Record<string, any>): Promise<any> {
        // @TODO: cache chainId?? purge on switch_networks

        // We have been destroyed; no operations are supported anymore
        if (this.destroyed) {
            return Promise.reject(makeError("provider destroyed; cancelled request", "UNSUPPORTED_OPERATION", { operation: method }));
        }

        const id = this.#nextId++;
        const promise = new Promise((resolve, reject) => {
            this.#payloads.push({
                resolve, reject,
                payload: { method, params, id, jsonrpc: "2.0" }
            });
        });

        // If there is not a pending drainTimer, set one
        this.#scheduleDrain();

        return <Promise<JsonRpcResult>>promise;
    }

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
    async getSigner(address?: number | string): Promise<JsonRpcSigner> {
        if (address == null) { address = 0; }

        const accountsPromise = this.send("eth_accounts", [ ]);

        // Account index
        if (typeof(address) === "number") {
            const accounts = <Array<string>>(await accountsPromise);
            if (address >= accounts.length) { throw new Error("no such account"); }
            return new JsonRpcSigner(this, accounts[address]);
        }

        const { accounts } = await resolveProperties({
            network: this.getNetwork(),
            accounts: accountsPromise
        });

        // Account address
        address = getAddress(address);
        for (const account of accounts) {
            if (getAddress(account) === address) {
                return new JsonRpcSigner(this, address);
            }
        }

        throw new Error("invalid account");
    }

    async listAccounts(): Promise<Array<JsonRpcSigner>> {
        const accounts: Array<string> = await this.send("eth_accounts", [ ]);
        return accounts.map((a) => new JsonRpcSigner(this, a));
    }

    destroy(): void {

        // Stop processing requests
        if (this.#drainTimer) {
            clearTimeout(this.#drainTimer);
            this.#drainTimer = null;
        }

        // Cancel all pending requests
        for (const { payload, reject } of this.#payloads) {
            reject(makeError("provider destroyed; cancelled request", "UNSUPPORTED_OPERATION", { operation: payload.method }));
        }

        this.#payloads = [ ];

        // Parent clean-up
        super.destroy();

    }
}

// @TODO: remove this in v7, it is not exported because this functionality
// is exposed in the JsonRpcApiProvider by setting polling to true. It should
// be safe to remove regardless, because it isn't reachable, but just in case.
/**
 *  @_ignore:
 */
export abstract class JsonRpcApiPollingProvider extends JsonRpcApiProvider {
    #pollingInterval: number;
    constructor(network?: Networkish, options?: JsonRpcApiProviderOptions) {
        super(network, options);

        let pollingInterval = this._getOption("pollingInterval");
        if (pollingInterval == null) { pollingInterval = defaultOptions.pollingInterval; }

        this.#pollingInterval = pollingInterval;
    }

    _getSubscriber(sub: Subscription): Subscriber {
        const subscriber = super._getSubscriber(sub);
        if (isPollable(subscriber)) {
            subscriber.pollingInterval = this.#pollingInterval;
        }
        return subscriber;
    }

    /**
     *  The polling interval (default: 4000 ms)
     */
    get pollingInterval(): number { return this.#pollingInterval; }
    set pollingInterval(value: number) {
        if (!Number.isInteger(value) || value < 0) { throw new Error("invalid interval"); }
        this.#pollingInterval = value;
        this._forEachSubscriber((sub) => {
            if (isPollable(sub)) {
                sub.pollingInterval = this.#pollingInterval;
            }
        });
    }
}

/**
 *  The JsonRpcProvider is one of the most common Providers,
 *  which performs all operations over HTTP (or HTTPS) requests.
 *
 *  Events are processed by polling the backend for the current block
 *  number; when it advances, all block-base events are then checked
 *  for updates.
 */
export class JsonRpcProvider extends JsonRpcApiPollingProvider {
    #connect: FetchRequest;

    constructor(url?: string | FetchRequest, network?: Networkish, options?: JsonRpcApiProviderOptions) {
        if (url == null) { url = "http:/\/localhost:8545"; }
        super(network, options);

        if (typeof(url) === "string") {
            this.#connect = new FetchRequest(url);
        } else {
            this.#connect = url.clone();
        }
    }

    _getConnection(): FetchRequest {
        return this.#connect.clone();
    }

    async send(method: string, params: Array<any> | Record<string, any>): Promise<any> {
        // All requests are over HTTP, so we can just start handling requests
        // We do this here rather than the constructor so that we don't send any
        // requests to the network (i.e. eth_chainId) until we absolutely have to.
        await this._start();

        return await super.send(method, params);
    }

    async _send(payload: JsonRpcPayload | Array<JsonRpcPayload>): Promise<Array<JsonRpcResult>> {
        // Configure a POST connection for the requested method
        const request = this._getConnection();
        request.body = JSON.stringify(payload);
        request.setHeader("content-type", "application/json");
        const response = await request.send();
        response.assertOk();

        let resp = response.bodyJson;
        if (!Array.isArray(resp)) { resp = [ resp ]; }

        return resp;
    }
}

function spelunkData(value: any): null | { message: string, data: string } {
    if (value == null) { return null; }

    // These *are* the droids we're looking for.
    if (typeof(value.message) === "string" && value.message.match(/revert/i) && isHexString(value.data)) {
        return { message: value.message, data: value.data };
    }

    // Spelunk further...
    if (typeof(value) === "object") {
        for (const key in value) {
            const result = spelunkData(value[key]);
            if (result) { return result; }
        }
        return null;
    }

    // Might be a JSON string we can further descend...
    if (typeof(value) === "string") {
        try {
            return spelunkData(JSON.parse(value));
        } catch (error) { }
    }

    return null;
}

function _spelunkMessage(value: any, result: Array<string>): void {
    if (value == null) { return; }

    // These *are* the droids we're looking for.
    if (typeof(value.message) === "string") {
        result.push(value.message);
    }

    // Spelunk further...
    if (typeof(value) === "object") {
        for (const key in value) {
            _spelunkMessage(value[key], result);
        }
    }

    // Might be a JSON string we can further descend...
    if (typeof(value) === "string") {
        try {
            return _spelunkMessage(JSON.parse(value), result);
        } catch (error) { }
    }
}

function spelunkMessage(value: any): Array<string> {
    const result: Array<string> = [ ];
    _spelunkMessage(value, result);
    return result;
}
