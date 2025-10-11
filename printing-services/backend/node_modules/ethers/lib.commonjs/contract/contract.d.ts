import { Interface } from "../abi/index.js";
import { Log, TransactionResponse } from "../providers/provider.js";
import { ContractTransactionResponse, EventLog } from "./wrappers.js";
import type { EventFragment, FunctionFragment, InterfaceAbi, ParamType } from "../abi/index.js";
import type { Addressable } from "../address/index.js";
import type { EventEmitterable, Listener } from "../utils/index.js";
import type { BlockTag, ContractRunner } from "../providers/index.js";
import type { ContractEventName, ContractInterface, ContractMethod, ContractEvent, ContractTransaction, WrappedFallback } from "./types.js";
/**
 *  @_ignore:
 */
export declare function copyOverrides<O extends string = "data" | "to">(arg: any, allowed?: Array<string>): Promise<Omit<ContractTransaction, O>>;
/**
 *  @_ignore:
 */
export declare function resolveArgs(_runner: null | ContractRunner, inputs: ReadonlyArray<ParamType>, args: Array<any>): Promise<Array<any>>;
declare const internal: unique symbol;
export declare class BaseContract implements Addressable, EventEmitterable<ContractEventName> {
    /**
     *  The target to connect to.
     *
     *  This can be an address, ENS name or any [[Addressable]], such as
     *  another contract. To get the resovled address, use the ``getAddress``
     *  method.
     */
    readonly target: string | Addressable;
    /**
     *  The contract Interface.
     */
    readonly interface: Interface;
    /**
     *  The connected runner. This is generally a [[Provider]] or a
     *  [[Signer]], which dictates what operations are supported.
     *
     *  For example, a **Contract** connected to a [[Provider]] may
     *  only execute read-only operations.
     */
    readonly runner: null | ContractRunner;
    /**
     *  All the Events available on this contract.
     */
    readonly filters: Record<string, ContractEvent>;
    /**
     *  @_ignore:
     */
    readonly [internal]: any;
    /**
     *  The fallback or receive function if any.
     */
    readonly fallback: null | WrappedFallback;
    /**
     *  Creates a new contract connected to %%target%% with the %%abi%% and
     *  optionally connected to a %%runner%% to perform operations on behalf
     *  of.
     */
    constructor(target: string | Addressable, abi: Interface | InterfaceAbi, runner?: null | ContractRunner, _deployTx?: null | TransactionResponse);
    /**
     *  Return a new Contract instance with the same target and ABI, but
     *  a different %%runner%%.
     */
    connect(runner: null | ContractRunner): BaseContract;
    /**
     *  Return a new Contract instance with the same ABI and runner, but
     *  a different %%target%%.
     */
    attach(target: string | Addressable): BaseContract;
    /**
     *  Return the resolved address of this Contract.
     */
    getAddress(): Promise<string>;
    /**
     *  Return the deployed bytecode or null if no bytecode is found.
     */
    getDeployedCode(): Promise<null | string>;
    /**
     *  Resolve to this Contract once the bytecode has been deployed, or
     *  resolve immediately if already deployed.
     */
    waitForDeployment(): Promise<this>;
    /**
     *  Return the transaction used to deploy this contract.
     *
     *  This is only available if this instance was returned from a
     *  [[ContractFactory]].
     */
    deploymentTransaction(): null | ContractTransactionResponse;
    /**
     *  Return the function for a given name. This is useful when a contract
     *  method name conflicts with a JavaScript name such as ``prototype`` or
     *  when using a Contract programatically.
     */
    getFunction<T extends ContractMethod = ContractMethod>(key: string | FunctionFragment): T;
    /**
     *  Return the event for a given name. This is useful when a contract
     *  event name conflicts with a JavaScript name such as ``prototype`` or
     *  when using a Contract programatically.
     */
    getEvent(key: string | EventFragment): ContractEvent;
    /**
     *  @_ignore:
     */
    queryTransaction(hash: string): Promise<Array<EventLog>>;
    /**
     *  Provide historic access to event data for %%event%% in the range
     *  %%fromBlock%% (default: ``0``) to %%toBlock%% (default: ``"latest"``)
     *  inclusive.
     */
    queryFilter(event: ContractEventName, fromBlock?: BlockTag, toBlock?: BlockTag): Promise<Array<EventLog | Log>>;
    /**
     *  Add an event %%listener%% for the %%event%%.
     */
    on(event: ContractEventName, listener: Listener): Promise<this>;
    /**
     *  Add an event %%listener%% for the %%event%%, but remove the listener
     *  after it is fired once.
     */
    once(event: ContractEventName, listener: Listener): Promise<this>;
    /**
     *  Emit an %%event%% calling all listeners with %%args%%.
     *
     *  Resolves to ``true`` if any listeners were called.
     */
    emit(event: ContractEventName, ...args: Array<any>): Promise<boolean>;
    /**
     *  Resolves to the number of listeners of %%event%% or the total number
     *  of listeners if unspecified.
     */
    listenerCount(event?: ContractEventName): Promise<number>;
    /**
     *  Resolves to the listeners subscribed to %%event%% or all listeners
     *  if unspecified.
     */
    listeners(event?: ContractEventName): Promise<Array<Listener>>;
    /**
     *  Remove the %%listener%% from the listeners for %%event%% or remove
     *  all listeners if unspecified.
     */
    off(event: ContractEventName, listener?: Listener): Promise<this>;
    /**
     *  Remove all the listeners for %%event%% or remove all listeners if
     *  unspecified.
     */
    removeAllListeners(event?: ContractEventName): Promise<this>;
    /**
     *  Alias for [on].
     */
    addListener(event: ContractEventName, listener: Listener): Promise<this>;
    /**
     *  Alias for [off].
     */
    removeListener(event: ContractEventName, listener: Listener): Promise<this>;
    /**
     *  Create a new Class for the %%abi%%.
     */
    static buildClass<T = ContractInterface>(abi: Interface | InterfaceAbi): new (target: string, runner?: null | ContractRunner) => BaseContract & Omit<T, keyof BaseContract>;
    /**
     *  Create a new BaseContract with a specified Interface.
     */
    static from<T = ContractInterface>(target: string, abi: Interface | InterfaceAbi, runner?: null | ContractRunner): BaseContract & Omit<T, keyof BaseContract>;
}
declare const Contract_base: new (target: string | Addressable, abi: Interface | InterfaceAbi, runner?: ContractRunner | null | undefined) => BaseContract & Omit<ContractInterface, keyof BaseContract>;
/**
 *  A [[BaseContract]] with no type guards on its methods or events.
 */
export declare class Contract extends Contract_base {
}
export {};
//# sourceMappingURL=contract.d.ts.map