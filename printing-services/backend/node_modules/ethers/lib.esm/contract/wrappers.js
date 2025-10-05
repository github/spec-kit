// import from provider.ts instead of index.ts to prevent circular dep
// from EtherscanProvider
import { Log, TransactionReceipt, TransactionResponse } from "../providers/provider.js";
import { defineProperties, EventPayload } from "../utils/index.js";
/**
 *  An **EventLog** contains additional properties parsed from the [[Log]].
 */
export class EventLog extends Log {
    /**
     *  The Contract Interface.
     */
    interface;
    /**
     *  The matching event.
     */
    fragment;
    /**
     *  The parsed arguments passed to the event by ``emit``.
     */
    args;
    /**
     * @_ignore:
     */
    constructor(log, iface, fragment) {
        super(log, log.provider);
        const args = iface.decodeEventLog(fragment, log.data, log.topics);
        defineProperties(this, { args, fragment, interface: iface });
    }
    /**
     *  The name of the event.
     */
    get eventName() { return this.fragment.name; }
    /**
     *  The signature of the event.
     */
    get eventSignature() { return this.fragment.format(); }
}
/**
 *  An **EventLog** contains additional properties parsed from the [[Log]].
 */
export class UndecodedEventLog extends Log {
    /**
     *  The error encounted when trying to decode the log.
     */
    error;
    /**
     * @_ignore:
     */
    constructor(log, error) {
        super(log, log.provider);
        defineProperties(this, { error });
    }
}
/**
 *  A **ContractTransactionReceipt** includes the parsed logs from a
 *  [[TransactionReceipt]].
 */
export class ContractTransactionReceipt extends TransactionReceipt {
    #iface;
    /**
     *  @_ignore:
     */
    constructor(iface, provider, tx) {
        super(tx, provider);
        this.#iface = iface;
    }
    /**
     *  The parsed logs for any [[Log]] which has a matching event in the
     *  Contract ABI.
     */
    get logs() {
        return super.logs.map((log) => {
            const fragment = log.topics.length ? this.#iface.getEvent(log.topics[0]) : null;
            if (fragment) {
                try {
                    return new EventLog(log, this.#iface, fragment);
                }
                catch (error) {
                    return new UndecodedEventLog(log, error);
                }
            }
            return log;
        });
    }
}
/**
 *  A **ContractTransactionResponse** will return a
 *  [[ContractTransactionReceipt]] when waited on.
 */
export class ContractTransactionResponse extends TransactionResponse {
    #iface;
    /**
     *  @_ignore:
     */
    constructor(iface, provider, tx) {
        super(tx, provider);
        this.#iface = iface;
    }
    /**
     *  Resolves once this transaction has been mined and has
     *  %%confirms%% blocks including it (default: ``1``) with an
     *  optional %%timeout%%.
     *
     *  This can resolve to ``null`` only if %%confirms%% is ``0``
     *  and the transaction has not been mined, otherwise this will
     *  wait until enough confirmations have completed.
     */
    async wait(confirms, timeout) {
        const receipt = await super.wait(confirms, timeout);
        if (receipt == null) {
            return null;
        }
        return new ContractTransactionReceipt(this.#iface, this.provider, receipt);
    }
}
/**
 *  A **ContractUnknownEventPayload** is included as the last parameter to
 *  Contract Events when the event does not match any events in the ABI.
 */
export class ContractUnknownEventPayload extends EventPayload {
    /**
     *  The log with no matching events.
     */
    log;
    /**
     *  @_event:
     */
    constructor(contract, listener, filter, log) {
        super(contract, listener, filter);
        defineProperties(this, { log });
    }
    /**
     *  Resolves to the block the event occured in.
     */
    async getBlock() {
        return await this.log.getBlock();
    }
    /**
     *  Resolves to the transaction the event occured in.
     */
    async getTransaction() {
        return await this.log.getTransaction();
    }
    /**
     *  Resolves to the transaction receipt the event occured in.
     */
    async getTransactionReceipt() {
        return await this.log.getTransactionReceipt();
    }
}
/**
 *  A **ContractEventPayload** is included as the last parameter to
 *  Contract Events when the event is known.
 */
export class ContractEventPayload extends ContractUnknownEventPayload {
    /**
     *  @_ignore:
     */
    constructor(contract, listener, filter, fragment, _log) {
        super(contract, listener, filter, new EventLog(_log, contract.interface, fragment));
        const args = contract.interface.decodeEventLog(fragment, this.log.data, this.log.topics);
        defineProperties(this, { args, fragment });
    }
    /**
     *  The event name.
     */
    get eventName() {
        return this.fragment.name;
    }
    /**
     *  The event signature.
     */
    get eventSignature() {
        return this.fragment.format();
    }
}
//# sourceMappingURL=wrappers.js.map