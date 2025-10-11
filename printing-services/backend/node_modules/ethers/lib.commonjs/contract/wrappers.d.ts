import { Block, Log, TransactionReceipt, TransactionResponse } from "../providers/provider.js";
import { EventPayload } from "../utils/index.js";
import type { EventFragment, Interface, Result } from "../abi/index.js";
import type { Listener } from "../utils/index.js";
import type { Provider } from "../providers/index.js";
import type { BaseContract } from "./contract.js";
import type { ContractEventName } from "./types.js";
/**
 *  An **EventLog** contains additional properties parsed from the [[Log]].
 */
export declare class EventLog extends Log {
    /**
     *  The Contract Interface.
     */
    readonly interface: Interface;
    /**
     *  The matching event.
     */
    readonly fragment: EventFragment;
    /**
     *  The parsed arguments passed to the event by ``emit``.
     */
    readonly args: Result;
    /**
     * @_ignore:
     */
    constructor(log: Log, iface: Interface, fragment: EventFragment);
    /**
     *  The name of the event.
     */
    get eventName(): string;
    /**
     *  The signature of the event.
     */
    get eventSignature(): string;
}
/**
 *  An **EventLog** contains additional properties parsed from the [[Log]].
 */
export declare class UndecodedEventLog extends Log {
    /**
     *  The error encounted when trying to decode the log.
     */
    readonly error: Error;
    /**
     * @_ignore:
     */
    constructor(log: Log, error: Error);
}
/**
 *  A **ContractTransactionReceipt** includes the parsed logs from a
 *  [[TransactionReceipt]].
 */
export declare class ContractTransactionReceipt extends TransactionReceipt {
    #private;
    /**
     *  @_ignore:
     */
    constructor(iface: Interface, provider: Provider, tx: TransactionReceipt);
    /**
     *  The parsed logs for any [[Log]] which has a matching event in the
     *  Contract ABI.
     */
    get logs(): Array<EventLog | Log>;
}
/**
 *  A **ContractTransactionResponse** will return a
 *  [[ContractTransactionReceipt]] when waited on.
 */
export declare class ContractTransactionResponse extends TransactionResponse {
    #private;
    /**
     *  @_ignore:
     */
    constructor(iface: Interface, provider: Provider, tx: TransactionResponse);
    /**
     *  Resolves once this transaction has been mined and has
     *  %%confirms%% blocks including it (default: ``1``) with an
     *  optional %%timeout%%.
     *
     *  This can resolve to ``null`` only if %%confirms%% is ``0``
     *  and the transaction has not been mined, otherwise this will
     *  wait until enough confirmations have completed.
     */
    wait(confirms?: number, timeout?: number): Promise<null | ContractTransactionReceipt>;
}
/**
 *  A **ContractUnknownEventPayload** is included as the last parameter to
 *  Contract Events when the event does not match any events in the ABI.
 */
export declare class ContractUnknownEventPayload extends EventPayload<ContractEventName> {
    /**
     *  The log with no matching events.
     */
    readonly log: Log;
    /**
     *  @_event:
     */
    constructor(contract: BaseContract, listener: null | Listener, filter: ContractEventName, log: Log);
    /**
     *  Resolves to the block the event occured in.
     */
    getBlock(): Promise<Block>;
    /**
     *  Resolves to the transaction the event occured in.
     */
    getTransaction(): Promise<TransactionResponse>;
    /**
     *  Resolves to the transaction receipt the event occured in.
     */
    getTransactionReceipt(): Promise<TransactionReceipt>;
}
/**
 *  A **ContractEventPayload** is included as the last parameter to
 *  Contract Events when the event is known.
 */
export declare class ContractEventPayload extends ContractUnknownEventPayload {
    /**
     *  The matching event.
     */
    readonly fragment: EventFragment;
    /**
     *  The log, with parsed properties.
     */
    readonly log: EventLog;
    /**
     *  The parsed arguments passed to the event by ``emit``.
     */
    readonly args: Result;
    /**
     *  @_ignore:
     */
    constructor(contract: BaseContract, listener: null | Listener, filter: ContractEventName, fragment: EventFragment, _log: Log);
    /**
     *  The event name.
     */
    get eventName(): string;
    /**
     *  The event signature.
     */
    get eventSignature(): string;
}
//# sourceMappingURL=wrappers.d.ts.map