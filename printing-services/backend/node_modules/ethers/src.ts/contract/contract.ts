import { Interface, Typed } from "../abi/index.js";
import { isAddressable, resolveAddress } from "../address/index.js";
// import from provider.ts instead of index.ts to prevent circular dep
// from EtherscanProvider
import { copyRequest, Log, TransactionResponse } from "../providers/provider.js";
import {
    defineProperties, getBigInt, isCallException, isHexString, resolveProperties,
    isError, makeError, assert, assertArgument
} from "../utils/index.js";

import {
    ContractEventPayload, ContractUnknownEventPayload,
    ContractTransactionResponse,
    EventLog, UndecodedEventLog
} from "./wrappers.js";

import type { EventFragment, FunctionFragment, InterfaceAbi, ParamType, Result } from "../abi/index.js";
import type { Addressable, NameResolver } from "../address/index.js";
import type { EventEmitterable, Listener } from "../utils/index.js";
import type {
    BlockTag, ContractRunner, Provider, TransactionRequest, TopicFilter
} from "../providers/index.js";

import type {
    BaseContractMethod,
    ContractEventName,
    ContractInterface,
    ContractMethodArgs,
    ContractMethod,
    ContractEventArgs,
    ContractEvent,
    ContractTransaction,
    DeferredTopicFilter,
    WrappedFallback
} from "./types.js";

const BN_0 = BigInt(0);

interface ContractRunnerCaller extends ContractRunner {
    call: (tx: TransactionRequest) => Promise<string>;
}

interface ContractRunnerEstimater extends ContractRunner {
    estimateGas: (tx: TransactionRequest) => Promise<bigint>;
}

interface ContractRunnerSender extends ContractRunner {
    sendTransaction: (tx: TransactionRequest) => Promise<TransactionResponse>;
}

interface ContractRunnerResolver extends ContractRunner {
    resolveName: (name: string | Addressable) => Promise<null | string>;
}

function canCall(value: any): value is ContractRunnerCaller {
    return (value && typeof(value.call) === "function");
}

function canEstimate(value: any): value is ContractRunnerEstimater {
    return (value && typeof(value.estimateGas) === "function");
}

function canResolve(value: any): value is ContractRunnerResolver {
    return (value && typeof(value.resolveName) === "function");
}

function canSend(value: any): value is ContractRunnerSender {
    return (value && typeof(value.sendTransaction) === "function");
}

function getResolver(value: any): undefined | NameResolver {
    if (value != null) {
        if (canResolve(value)) { return value; }
        if (value.provider) { return value.provider; }
    }
    return undefined;
}

class PreparedTopicFilter implements DeferredTopicFilter {
    #filter: Promise<TopicFilter>;
    readonly fragment!: EventFragment;

    constructor(contract: BaseContract, fragment: EventFragment, args: Array<any>) {
        defineProperties<PreparedTopicFilter>(this, { fragment });
        if (fragment.inputs.length < args.length) {
            throw new Error("too many arguments");
        }

        // Recursively descend into args and resolve any addresses
        const runner = getRunner(contract.runner, "resolveName");
        const resolver = canResolve(runner) ? runner: null;
        this.#filter = (async function() {
            const resolvedArgs = await Promise.all(fragment.inputs.map((param, index) => {
                const arg = args[index];
                if (arg == null) { return null; }

                return param.walkAsync(args[index], (type, value) => {
                    if (type === "address") {
                        if (Array.isArray(value)) {
                            return Promise.all(value.map((v) => resolveAddress(v, resolver)));
                        }
                        return resolveAddress(value, resolver);
                    }
                    return value;
                });
            }));

            return contract.interface.encodeFilterTopics(fragment, resolvedArgs);
        })();
    }

    getTopicFilter(): Promise<TopicFilter> {
        return this.#filter;
    }
}


// A = Arguments passed in as a tuple
// R = The result type of the call (i.e. if only one return type,
//     the qualified type, otherwise Result)
// D = The type the default call will return (i.e. R for view/pure,
//     TransactionResponse otherwise)
//export interface ContractMethod<A extends Array<any> = Array<any>, R = any, D extends R | ContractTransactionResponse = ContractTransactionResponse> {

function getRunner<T extends ContractRunner>(value: any, feature: keyof ContractRunner): null | T {
    if (value == null) { return null; }
    if (typeof(value[feature]) === "function") { return value; }
    if (value.provider && typeof(value.provider[feature]) === "function") {
        return value.provider;
    }
    return null;
}

function getProvider(value: null | ContractRunner): null | Provider {
    if (value == null) { return null; }
    return value.provider || null;
}

/**
 *  @_ignore:
 */
export async function copyOverrides<O extends string = "data" | "to">(arg: any, allowed?: Array<string>): Promise<Omit<ContractTransaction, O>> {

    // Make sure the overrides passed in are a valid overrides object
    const _overrides = Typed.dereference(arg, "overrides");
    assertArgument(typeof(_overrides) === "object", "invalid overrides parameter", "overrides", arg);

    // Create a shallow copy (we'll deep-ify anything needed during normalizing)
    const overrides = copyRequest(_overrides);

    assertArgument(overrides.to == null || (allowed || [ ]).indexOf("to") >= 0,
      "cannot override to", "overrides.to", overrides.to);
    assertArgument(overrides.data == null || (allowed || [ ]).indexOf("data") >= 0,
      "cannot override data", "overrides.data", overrides.data);

    // Resolve any from
    if (overrides.from) { overrides.from = overrides.from; }

    return <Omit<ContractTransaction, O>>overrides;
}

/**
 *  @_ignore:
 */
export async function resolveArgs(_runner: null | ContractRunner, inputs: ReadonlyArray<ParamType>, args: Array<any>): Promise<Array<any>> {
    // Recursively descend into args and resolve any addresses
    const runner = getRunner(_runner, "resolveName");
    const resolver = canResolve(runner) ? runner: null;
    return await Promise.all(inputs.map((param, index) => {
        return param.walkAsync(args[index], (type, value) => {
            value = Typed.dereference(value, type);
            if (type === "address") { return resolveAddress(value, resolver); }
            return value;
        });
    }));
}

function buildWrappedFallback(contract: BaseContract): WrappedFallback {

    const populateTransaction = async function(overrides?: Omit<TransactionRequest, "to">): Promise<ContractTransaction> {
        // If an overrides was passed in, copy it and normalize the values

        const tx: ContractTransaction = <any>(await copyOverrides<"data">(overrides, [ "data" ]));
        tx.to = await contract.getAddress();

        if (tx.from) {
            tx.from = await resolveAddress(tx.from, getResolver(contract.runner));
        }

        const iface = contract.interface;

        const noValue = (getBigInt((tx.value || BN_0), "overrides.value") === BN_0);
        const noData = ((tx.data || "0x") === "0x");

        if (iface.fallback && !iface.fallback.payable && iface.receive && !noData && !noValue) {
            assertArgument(false, "cannot send data to receive or send value to non-payable fallback", "overrides", overrides);
        }

        assertArgument(iface.fallback || noData,
          "cannot send data to receive-only contract", "overrides.data", tx.data);

        // Only allow payable contracts to set non-zero value
        const payable = iface.receive || (iface.fallback && iface.fallback.payable);
        assertArgument(payable || noValue,
          "cannot send value to non-payable fallback", "overrides.value", tx.value);

        // Only allow fallback contracts to set non-empty data
        assertArgument(iface.fallback || noData,
          "cannot send data to receive-only contract", "overrides.data", tx.data);

        return tx;
    }

    const staticCall = async function(overrides?: Omit<TransactionRequest, "to">): Promise<string> {
        const runner = getRunner(contract.runner, "call");
        assert(canCall(runner), "contract runner does not support calling",
            "UNSUPPORTED_OPERATION", { operation: "call" });

        const tx = await populateTransaction(overrides);

        try {
            return await runner.call(tx);
        } catch (error: any) {
            if (isCallException(error) && error.data) {
                throw contract.interface.makeError(error.data, tx);
            }
            throw error;
        }
    }

    const send = async function(overrides?: Omit<TransactionRequest, "to">): Promise<ContractTransactionResponse> {
        const runner = contract.runner;
        assert(canSend(runner), "contract runner does not support sending transactions",
            "UNSUPPORTED_OPERATION", { operation: "sendTransaction" });

        const tx = await runner.sendTransaction(await populateTransaction(overrides));
        const provider = getProvider(contract.runner);
        // @TODO: the provider can be null; make a custom dummy provider that will throw a
        // meaningful error
        return new ContractTransactionResponse(contract.interface, <Provider>provider, tx);
    }

    const estimateGas = async function(overrides?: Omit<TransactionRequest, "to">): Promise<bigint> {
        const runner = getRunner(contract.runner, "estimateGas");
        assert(canEstimate(runner), "contract runner does not support gas estimation",
            "UNSUPPORTED_OPERATION", { operation: "estimateGas" });

        return await runner.estimateGas(await populateTransaction(overrides));
    }

    const method = async (overrides?: Omit<TransactionRequest, "to">) => {
        return await send(overrides);
    };

    defineProperties<any>(method, {
        _contract: contract,

        estimateGas,
        populateTransaction,
        send, staticCall
    });

    return <WrappedFallback>method;
}

function buildWrappedMethod<A extends Array<any> = Array<any>, R = any, D extends R | ContractTransactionResponse = ContractTransactionResponse>(contract: BaseContract, key: string): BaseContractMethod<A, R, D> {

    const getFragment = function(...args: ContractMethodArgs<A>): FunctionFragment {
        const fragment = contract.interface.getFunction(key, args);
        assert(fragment, "no matching fragment", "UNSUPPORTED_OPERATION", {
            operation: "fragment",
            info: { key, args }
        });
        return fragment;
    }

    const populateTransaction = async function(...args: ContractMethodArgs<A>): Promise<ContractTransaction> {
        const fragment = getFragment(...args);

        // If an overrides was passed in, copy it and normalize the values
        let overrides: Omit<ContractTransaction, "data" | "to"> = { };
        if (fragment.inputs.length + 1 === args.length) {
            overrides = await copyOverrides(args.pop());

            if (overrides.from) {
                overrides.from = await resolveAddress(overrides.from, getResolver(contract.runner));
            }
        }

        if (fragment.inputs.length !== args.length) {
            throw new Error("internal error: fragment inputs doesn't match arguments; should not happen");
        }

        const resolvedArgs = await resolveArgs(contract.runner, fragment.inputs, args);

        return Object.assign({ }, overrides, await resolveProperties({
            to: contract.getAddress(),
            data: contract.interface.encodeFunctionData(fragment, resolvedArgs)
        }));
    }

    const staticCall = async function(...args: ContractMethodArgs<A>): Promise<R> {
        const result = await staticCallResult(...args);
        if (result.length === 1) { return result[0]; }
        return <R><unknown>result;
    }

    const send = async function(...args: ContractMethodArgs<A>): Promise<ContractTransactionResponse> {
        const runner = contract.runner;
        assert(canSend(runner), "contract runner does not support sending transactions",
            "UNSUPPORTED_OPERATION", { operation: "sendTransaction" });

        const tx = await runner.sendTransaction(await populateTransaction(...args));
        const provider = getProvider(contract.runner);
        // @TODO: the provider can be null; make a custom dummy provider that will throw a
        // meaningful error
        return new ContractTransactionResponse(contract.interface, <Provider>provider, tx);
    }

    const estimateGas = async function(...args: ContractMethodArgs<A>): Promise<bigint> {
        const runner = getRunner(contract.runner, "estimateGas");
        assert(canEstimate(runner), "contract runner does not support gas estimation",
            "UNSUPPORTED_OPERATION", { operation: "estimateGas" });

        return await runner.estimateGas(await populateTransaction(...args));
    }

    const staticCallResult = async function(...args: ContractMethodArgs<A>): Promise<Result> {
        const runner = getRunner(contract.runner, "call");
        assert(canCall(runner), "contract runner does not support calling",
            "UNSUPPORTED_OPERATION", { operation: "call" });

        const tx = await populateTransaction(...args);

        let result = "0x";
        try {
            result = await runner.call(tx);
        } catch (error: any) {
            if (isCallException(error) && error.data) {
                throw contract.interface.makeError(error.data, tx);
            }
            throw error;
        }

        const fragment = getFragment(...args);
        return contract.interface.decodeFunctionResult(fragment, result);
    };

    const method = async (...args: ContractMethodArgs<A>) => {
        const fragment = getFragment(...args);
        if (fragment.constant) { return await staticCall(...args); }
        return await send(...args);
    };

    defineProperties<any>(method, {
        name: contract.interface.getFunctionName(key),
        _contract: contract, _key: key,

        getFragment,

        estimateGas,
        populateTransaction,
        send, staticCall, staticCallResult,
    });

    // Only works on non-ambiguous keys (refined fragment is always non-ambiguous)
    Object.defineProperty(method, "fragment", {
        configurable: false,
        enumerable: true,
        get: () => {
            const fragment = contract.interface.getFunction(key);
            assert(fragment, "no matching fragment", "UNSUPPORTED_OPERATION", {
                operation: "fragment",
                info: { key }
            });
            return fragment;
        }
    });

    return <BaseContractMethod<A, R, D>>method;
}

function buildWrappedEvent<A extends Array<any> = Array<any>>(contract: BaseContract, key: string): ContractEvent<A> {

    const getFragment = function(...args: ContractEventArgs<A>): EventFragment {
        const fragment = contract.interface.getEvent(key, args);

        assert(fragment, "no matching fragment", "UNSUPPORTED_OPERATION", {
            operation: "fragment",
            info: { key, args }
        });

        return fragment;
    }

    const method = function(...args: ContractMethodArgs<A>): PreparedTopicFilter {
        return new PreparedTopicFilter(contract, getFragment(...args), args);
    };

    defineProperties<any>(method, {
        name: contract.interface.getEventName(key),
        _contract: contract, _key: key,

        getFragment
    });

    // Only works on non-ambiguous keys (refined fragment is always non-ambiguous)
    Object.defineProperty(method, "fragment", {
        configurable: false,
        enumerable: true,
        get: () => {
            const fragment = contract.interface.getEvent(key);

            assert(fragment, "no matching fragment", "UNSUPPORTED_OPERATION", {
                operation: "fragment",
                info: { key }
            });

            return fragment;
        }
    });

    return <ContractEvent<A>><unknown>method;
}

type Sub = {
    tag: string;
    listeners: Array<{ listener: Listener, once: boolean }>,
    start: () => void;
    stop: () => void;
};


// The combination of TypeScrype, Private Fields and Proxies makes
// the world go boom; so we hide variables with some trickery keeping
// a symbol attached to each BaseContract which its sub-class (even
// via a Proxy) can reach and use to look up its internal values.

const internal = Symbol.for("_ethersInternal_contract");
type Internal = {
    addrPromise: Promise<string>;
    addr: null | string;

    deployTx: null | ContractTransactionResponse;

    subs: Map<string, Sub>;
};

const internalValues: WeakMap<BaseContract, Internal> = new WeakMap();

function setInternal(contract: BaseContract, values: Internal): void {
    internalValues.set(contract[internal], values);
}

function getInternal(contract: BaseContract): Internal {
    return internalValues.get(contract[internal]) as Internal;
}

function isDeferred(value: any): value is DeferredTopicFilter {
    return (value && typeof(value) === "object" && ("getTopicFilter" in value) &&
      (typeof(value.getTopicFilter) === "function") && value.fragment);
}

async function getSubInfo(contract: BaseContract, event: ContractEventName): Promise<{ fragment: null | EventFragment, tag: string, topics: TopicFilter }> {
    let topics: Array<null | string | Array<string>>;
    let fragment: null | EventFragment = null;

    // Convert named events to topicHash and get the fragment for
    // events which need deconstructing.

    if (Array.isArray(event)) {
        const topicHashify = function(name: string): string {
            if (isHexString(name, 32)) { return name; }
            const fragment = contract.interface.getEvent(name);
            assertArgument(fragment, "unknown fragment", "name", name);
            return fragment.topicHash;
        }

        // Array of Topics and Names; e.g. `[ "0x1234...89ab", "Transfer(address)" ]`
        topics = event.map((e) => {
            if (e == null) { return null; }
            if (Array.isArray(e)) { return e.map(topicHashify); }
            return topicHashify(e);
        });

    } else if (event === "*") {
        topics = [ null ];

    } else if (typeof(event) === "string") {
        if (isHexString(event, 32)) {
            // Topic Hash
            topics = [ event ];
        } else {
           // Name or Signature; e.g. `"Transfer", `"Transfer(address)"`
            fragment = contract.interface.getEvent(event);
            assertArgument(fragment, "unknown fragment", "event", event);
            topics = [ fragment.topicHash ];
        }

    } else if (isDeferred(event)) {
        // Deferred Topic Filter; e.g. `contract.filter.Transfer(from)`
        topics = await event.getTopicFilter();

    } else if ("fragment" in event) {
        // ContractEvent; e.g. `contract.filter.Transfer`
        fragment = event.fragment;
        topics = [ fragment.topicHash ];

    } else {
        assertArgument(false, "unknown event name", "event", event);
    }

    // Normalize topics and sort TopicSets
    topics = topics.map((t) => {
        if (t == null) { return null; }
        if (Array.isArray(t)) {
            const items = Array.from(new Set(t.map((t) => t.toLowerCase())).values());
            if (items.length === 1) { return items[0]; }
            items.sort();
            return items;
        }
        return t.toLowerCase();
    });

    const tag = topics.map((t) => {
        if (t == null) { return "null"; }
        if (Array.isArray(t)) { return t.join("|"); }
        return t;
    }).join("&");

    return { fragment, tag, topics }
}

async function hasSub(contract: BaseContract, event: ContractEventName): Promise<null | Sub> {
    const { subs } = getInternal(contract);
    return subs.get((await getSubInfo(contract, event)).tag) || null;
}

async function getSub(contract: BaseContract, operation: string, event: ContractEventName): Promise<Sub> {
    // Make sure our runner can actually subscribe to events
    const provider = getProvider(contract.runner);
    assert(provider, "contract runner does not support subscribing",
        "UNSUPPORTED_OPERATION", { operation });

    const { fragment, tag, topics } = await getSubInfo(contract, event);

    const { addr, subs } = getInternal(contract);

    let sub = subs.get(tag);
    if (!sub) {
        const address: string | Addressable = (addr ? addr: contract);
        const filter = { address, topics };
        const listener = (log: Log) => {
            let foundFragment = fragment;
            if (foundFragment == null) {
                try {
                    foundFragment = contract.interface.getEvent(log.topics[0]);
                } catch (error) { }
            }

            // If fragment is null, we do not deconstruct the args to emit

            if (foundFragment) {
                const _foundFragment = foundFragment;
                const args = fragment ? contract.interface.decodeEventLog(fragment, log.data, log.topics): [ ];
                emit(contract, event, args, (listener: null | Listener) => {
                    return new ContractEventPayload(contract, listener, event, _foundFragment, log);
                });
            } else {
                emit(contract, event, [ ], (listener: null | Listener) => {
                    return new ContractUnknownEventPayload(contract, listener, event, log);
                });
            }
        };

        let starting: Array<Promise<any>> = [ ];
        const start = () => {
            if (starting.length) { return; }
            starting.push(provider.on(filter, listener));
        };

        const stop = async () => {
            if (starting.length == 0) { return; }

            let started = starting;
            starting = [ ];
            await Promise.all(started);
            provider.off(filter, listener);
        };

        sub = { tag, listeners: [ ], start, stop };
        subs.set(tag, sub);
    }
    return sub;
}

// We use this to ensure one emit resolves before firing the next to
// ensure correct ordering (note this cannot throw and just adds the
// notice to the event queu using setTimeout).
let lastEmit: Promise<any> = Promise.resolve();

type PayloadFunc = (listener: null | Listener) => ContractUnknownEventPayload;

async function _emit(contract: BaseContract, event: ContractEventName, args: Array<any>, payloadFunc: null | PayloadFunc): Promise<boolean> {
    await lastEmit;

    const sub = await hasSub(contract, event);
    if (!sub) { return false; }

    const count = sub.listeners.length;
    sub.listeners = sub.listeners.filter(({ listener, once }) => {
        const passArgs = Array.from(args);
        if (payloadFunc) {
            passArgs.push(payloadFunc(once ? null: listener));
        }
        try {
            listener.call(contract, ...passArgs);
        } catch (error) { }
        return !once;
    });

    if (sub.listeners.length === 0) {
        sub.stop();
        getInternal(contract).subs.delete(sub.tag);
    }

    return (count > 0);
}

async function emit(contract: BaseContract, event: ContractEventName, args: Array<any>, payloadFunc: null | PayloadFunc): Promise<boolean> {
    try {
        await lastEmit;
    } catch (error) { }

    const resultPromise = _emit(contract, event, args, payloadFunc);
    lastEmit = resultPromise;
    return await resultPromise;
}

const passProperties = [ "then" ];
export class BaseContract implements Addressable, EventEmitterable<ContractEventName> {
    /**
     *  The target to connect to.
     *
     *  This can be an address, ENS name or any [[Addressable]], such as
     *  another contract. To get the resovled address, use the ``getAddress``
     *  method.
     */
    readonly target!: string | Addressable;

    /**
     *  The contract Interface.
     */
    readonly interface!: Interface;

    /**
     *  The connected runner. This is generally a [[Provider]] or a
     *  [[Signer]], which dictates what operations are supported.
     *
     *  For example, a **Contract** connected to a [[Provider]] may
     *  only execute read-only operations.
     */
    readonly runner!: null | ContractRunner;

    /**
     *  All the Events available on this contract.
     */
    readonly filters!: Record<string, ContractEvent>;

    /**
     *  @_ignore:
     */
    readonly [internal]: any;

    /**
     *  The fallback or receive function if any.
     */
    readonly fallback!: null | WrappedFallback;

    /**
     *  Creates a new contract connected to %%target%% with the %%abi%% and
     *  optionally connected to a %%runner%% to perform operations on behalf
     *  of.
     */
    constructor(target: string | Addressable, abi: Interface | InterfaceAbi, runner?: null | ContractRunner, _deployTx?: null | TransactionResponse) {
        assertArgument(typeof(target) === "string" || isAddressable(target),
            "invalid value for Contract target", "target", target);

        if (runner == null) { runner = null; }
        const iface = Interface.from(abi);
        defineProperties<BaseContract>(this, { target, runner, interface: iface });

        Object.defineProperty(this, internal, { value: { } });

        let addrPromise;
        let addr: null | string = null;

        let deployTx: null | ContractTransactionResponse = null;
        if (_deployTx) {
            const provider = getProvider(runner);
            // @TODO: the provider can be null; make a custom dummy provider that will throw a
            // meaningful error
            deployTx = new ContractTransactionResponse(this.interface, <Provider>provider, _deployTx);
        }

        let subs = new Map();

        // Resolve the target as the address
        if (typeof(target) === "string") {
            if (isHexString(target)) {
                addr = target;
                addrPromise = Promise.resolve(target);

            } else {
                const resolver = getRunner(runner, "resolveName");
                if (!canResolve(resolver)) {
                    throw makeError("contract runner does not support name resolution", "UNSUPPORTED_OPERATION", {
                        operation: "resolveName"
                    });
                }

                addrPromise = resolver.resolveName(target).then((addr) => {
                    if (addr == null) {
                        throw makeError("an ENS name used for a contract target must be correctly configured", "UNCONFIGURED_NAME", {
                            value: target
                        });
                    }
                    getInternal(this).addr = addr;
                    return addr;
                });
            }
        } else {
            addrPromise = target.getAddress().then((addr) => {
                if (addr == null) { throw new Error("TODO"); }
                getInternal(this).addr = addr;
                return addr;
            });
        }

        // Set our private values
        setInternal(this, { addrPromise, addr, deployTx, subs });

        // Add the event filters
        const filters = new Proxy({ }, {
            get: (target, prop, receiver) => {
                // Pass important checks (like `then` for Promise) through
                if (typeof(prop) === "symbol" || passProperties.indexOf(prop) >= 0) {
                    return Reflect.get(target, prop, receiver);
                }

                try {
                    return this.getEvent(prop);
                } catch (error) {
                    if (!isError(error, "INVALID_ARGUMENT") || error.argument !== "key") {
                        throw error;
                    }
                }

                return undefined;
            },
            has: (target, prop) => {
                // Pass important checks (like `then` for Promise) through
                if (passProperties.indexOf(<string>prop) >= 0) {
                    return Reflect.has(target, prop);
                }

                return Reflect.has(target, prop) || this.interface.hasEvent(String(prop));
            }
        });
        defineProperties<BaseContract>(this, { filters });

        defineProperties<BaseContract>(this, {
            fallback: ((iface.receive || iface.fallback) ? (buildWrappedFallback(this)): null)
        });

        // Return a Proxy that will respond to functions
        return new Proxy(this, {
            get: (target, prop, receiver) => {
                if (typeof(prop) === "symbol" || prop in target || passProperties.indexOf(prop) >= 0) {
                    return Reflect.get(target, prop, receiver);
                }

                // Undefined properties should return undefined
                try {
                    return target.getFunction(prop);
                } catch (error) {
                    if (!isError(error, "INVALID_ARGUMENT") || error.argument !== "key") {
                        throw error;
                    }
                }

                return undefined;
            },
            has: (target, prop) => {
                if (typeof(prop) === "symbol" || prop in target || passProperties.indexOf(prop) >= 0) {
                    return Reflect.has(target, prop);
                }

                return target.interface.hasFunction(prop);
            }
        });

    }

    /**
     *  Return a new Contract instance with the same target and ABI, but
     *  a different %%runner%%.
     */
    connect(runner: null | ContractRunner): BaseContract {
        return new BaseContract(this.target, this.interface, runner);
    }

    /**
     *  Return a new Contract instance with the same ABI and runner, but
     *  a different %%target%%.
     */
    attach(target: string | Addressable): BaseContract {
        return new BaseContract(target, this.interface, this.runner);
    }

    /**
     *  Return the resolved address of this Contract.
     */
    async getAddress(): Promise<string> { return await getInternal(this).addrPromise; }

    /**
     *  Return the deployed bytecode or null if no bytecode is found.
     */
    async getDeployedCode(): Promise<null | string> {
        const provider = getProvider(this.runner);
        assert(provider, "runner does not support .provider",
            "UNSUPPORTED_OPERATION", { operation: "getDeployedCode" });

        const code = await provider.getCode(await this.getAddress());
        if (code === "0x") { return null; }
        return code;
    }

    /**
     *  Resolve to this Contract once the bytecode has been deployed, or
     *  resolve immediately if already deployed.
     */
    async waitForDeployment(): Promise<this> {
        // We have the deployement transaction; just use that (throws if deployement fails)
        const deployTx = this.deploymentTransaction();
        if (deployTx) {
            await deployTx.wait();
            return this;
        }

        // Check for code
        const code = await this.getDeployedCode();
        if (code != null) { return this; }

        // Make sure we can subscribe to a provider event
        const provider = getProvider(this.runner);
        assert(provider != null, "contract runner does not support .provider",
            "UNSUPPORTED_OPERATION", { operation: "waitForDeployment" });

        return new Promise((resolve, reject) => {
            const checkCode = async () => {
                try {
                    const code = await this.getDeployedCode();
                    if (code != null) { return resolve(this); }
                    provider.once("block", checkCode);
                } catch (error) {
                    reject(error);
                }
            };
            checkCode();
        });
    }

    /**
     *  Return the transaction used to deploy this contract.
     *
     *  This is only available if this instance was returned from a
     *  [[ContractFactory]].
     */
    deploymentTransaction(): null | ContractTransactionResponse {
        return getInternal(this).deployTx;
    }

    /**
     *  Return the function for a given name. This is useful when a contract
     *  method name conflicts with a JavaScript name such as ``prototype`` or
     *  when using a Contract programatically.
     */
    getFunction<T extends ContractMethod = ContractMethod>(key: string | FunctionFragment): T {
        if (typeof(key) !== "string") { key = key.format(); }
        const func = buildWrappedMethod(this, key);
        return <T>func;
    }

    /**
     *  Return the event for a given name. This is useful when a contract
     *  event name conflicts with a JavaScript name such as ``prototype`` or
     *  when using a Contract programatically.
     */
    getEvent(key: string | EventFragment): ContractEvent {
        if (typeof(key) !== "string") { key = key.format(); }
        return buildWrappedEvent(this, key);
    }

    /**
     *  @_ignore:
     */
    async queryTransaction(hash: string): Promise<Array<EventLog>> {
        throw new Error("@TODO");
    }

    /*
    // @TODO: this is a non-backwards compatible change, but will be added
    //        in v7 and in a potential SmartContract class in an upcoming
    //        v6 release
    async getTransactionReceipt(hash: string): Promise<null | ContractTransactionReceipt> {
        const provider = getProvider(this.runner);
        assert(provider, "contract runner does not have a provider",
            "UNSUPPORTED_OPERATION", { operation: "queryTransaction" });

        const receipt = await provider.getTransactionReceipt(hash);
        if (receipt == null) { return null; }

        return new ContractTransactionReceipt(this.interface, provider, receipt);
    }
    */

    /**
     *  Provide historic access to event data for %%event%% in the range
     *  %%fromBlock%% (default: ``0``) to %%toBlock%% (default: ``"latest"``)
     *  inclusive.
     */
    async queryFilter(event: ContractEventName, fromBlock?: BlockTag, toBlock?: BlockTag): Promise<Array<EventLog | Log>> {
        if (fromBlock == null) { fromBlock = 0; }
        if (toBlock == null) { toBlock = "latest"; }
        const { addr, addrPromise } = getInternal(this);
        const address = (addr ? addr: (await addrPromise));
        const { fragment, topics } = await getSubInfo(this, event);
        const filter = { address, topics, fromBlock, toBlock };

        const provider = getProvider(this.runner);
        assert(provider, "contract runner does not have a provider",
            "UNSUPPORTED_OPERATION", { operation: "queryFilter" });

        return (await provider.getLogs(filter)).map((log) => {
            let foundFragment = fragment;
            if (foundFragment == null) {
                try {
                    foundFragment = this.interface.getEvent(log.topics[0]);
                } catch (error) { }
            }

            if (foundFragment) {
                try {
                    return new EventLog(log, this.interface, foundFragment);
                } catch (error: any) {
                    return new UndecodedEventLog(log, error);
                }
            }

            return new Log(log, provider);
        });
    }

    /**
     *  Add an event %%listener%% for the %%event%%.
     */
    async on(event: ContractEventName, listener: Listener): Promise<this> {
        const sub = await getSub(this, "on", event);
        sub.listeners.push({ listener, once: false });
        sub.start();
        return this;
    }

    /**
     *  Add an event %%listener%% for the %%event%%, but remove the listener
     *  after it is fired once.
     */
    async once(event: ContractEventName, listener: Listener): Promise<this> {
        const sub = await getSub(this, "once", event);
        sub.listeners.push({ listener, once: true });
        sub.start();
        return this;
    }

    /**
     *  Emit an %%event%% calling all listeners with %%args%%.
     *
     *  Resolves to ``true`` if any listeners were called.
     */
    async emit(event: ContractEventName, ...args: Array<any>): Promise<boolean> {
        return await emit(this, event, args, null);
    }

    /**
     *  Resolves to the number of listeners of %%event%% or the total number
     *  of listeners if unspecified.
     */
    async listenerCount(event?: ContractEventName): Promise<number> {
        if (event) {
            const sub = await hasSub(this, event);
            if (!sub) { return 0; }
            return sub.listeners.length;
        }

        const { subs } = getInternal(this);

        let total = 0;
        for (const { listeners } of subs.values()) {
            total += listeners.length;
        }
        return total;
    }

    /**
     *  Resolves to the listeners subscribed to %%event%% or all listeners
     *  if unspecified.
     */
    async listeners(event?: ContractEventName): Promise<Array<Listener>> {
        if (event) {
            const sub = await hasSub(this, event);
            if (!sub) { return [ ]; }
            return sub.listeners.map(({ listener }) => listener);
        }

        const { subs } = getInternal(this);

        let result: Array<Listener> = [ ];
        for (const { listeners } of subs.values()) {
            result = result.concat(listeners.map(({ listener }) => listener));
        }
        return result;
    }

    /**
     *  Remove the %%listener%% from the listeners for %%event%% or remove
     *  all listeners if unspecified.
     */
    async off(event: ContractEventName, listener?: Listener): Promise<this> {
        const sub = await hasSub(this, event);
        if (!sub) { return this; }

        if (listener) {
            const index = sub.listeners.map(({ listener }) => listener).indexOf(listener);
            if (index >= 0) { sub.listeners.splice(index, 1); }
        }

        if (listener == null || sub.listeners.length === 0) {
            sub.stop();
            getInternal(this).subs.delete(sub.tag);
        }

        return this;
    }

    /**
     *  Remove all the listeners for %%event%% or remove all listeners if
     *  unspecified.
     */
    async removeAllListeners(event?: ContractEventName): Promise<this> {
        if (event) {
            const sub = await hasSub(this, event);
            if (!sub) { return this; }
            sub.stop();
            getInternal(this).subs.delete(sub.tag);
        } else {
            const { subs } = getInternal(this);
            for (const { tag, stop } of subs.values()) {
                stop();
                subs.delete(tag);
            }
        }

        return this;
    }

    /**
     *  Alias for [on].
     */
    async addListener(event: ContractEventName, listener: Listener): Promise<this> {
        return await this.on(event, listener);
    }

    /**
     *  Alias for [off].
     */
    async removeListener(event: ContractEventName, listener: Listener): Promise<this> {
        return await this.off(event, listener);
    }

    /**
     *  Create a new Class for the %%abi%%.
     */
    static buildClass<T = ContractInterface>(abi: Interface | InterfaceAbi): new (target: string, runner?: null | ContractRunner) => BaseContract & Omit<T, keyof BaseContract> {
        class CustomContract extends BaseContract {
            constructor(address: string, runner: null | ContractRunner = null) {
                super(address, abi, runner);
            }
        }
        return CustomContract as any;
    };

    /**
     *  Create a new BaseContract with a specified Interface.
     */
    static from<T = ContractInterface>(target: string, abi: Interface | InterfaceAbi, runner?: null | ContractRunner): BaseContract & Omit<T, keyof BaseContract> {
        if (runner == null) { runner = null; }
        const contract = new this(target, abi, runner );
        return contract as any;
    }
}

function _ContractBase(): new (target: string | Addressable, abi: Interface | InterfaceAbi, runner?: null | ContractRunner) => BaseContract & Omit<ContractInterface, keyof BaseContract> {
    return BaseContract as any;
}

/**
 *  A [[BaseContract]] with no type guards on its methods or events.
 */
export class Contract extends _ContractBase() { }
