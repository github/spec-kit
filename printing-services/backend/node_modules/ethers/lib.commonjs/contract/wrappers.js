"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ContractEventPayload = exports.ContractUnknownEventPayload = exports.ContractTransactionResponse = exports.ContractTransactionReceipt = exports.UndecodedEventLog = exports.EventLog = void 0;
// import from provider.ts instead of index.ts to prevent circular dep
// from EtherscanProvider
const provider_js_1 = require("../providers/provider.js");
const index_js_1 = require("../utils/index.js");
/**
 *  An **EventLog** contains additional properties parsed from the [[Log]].
 */
class EventLog extends provider_js_1.Log {
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
        (0, index_js_1.defineProperties)(this, { args, fragment, interface: iface });
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
exports.EventLog = EventLog;
/**
 *  An **EventLog** contains additional properties parsed from the [[Log]].
 */
class UndecodedEventLog extends provider_js_1.Log {
    /**
     *  The error encounted when trying to decode the log.
     */
    error;
    /**
     * @_ignore:
     */
    constructor(log, error) {
        super(log, log.provider);
        (0, index_js_1.defineProperties)(this, { error });
    }
}
exports.UndecodedEventLog = UndecodedEventLog;
/**
 *  A **ContractTransactionReceipt** includes the parsed logs from a
 *  [[TransactionReceipt]].
 */
class ContractTransactionReceipt extends provider_js_1.TransactionReceipt {
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
exports.ContractTransactionReceipt = ContractTransactionReceipt;
/**
 *  A **ContractTransactionResponse** will return a
 *  [[ContractTransactionReceipt]] when waited on.
 */
class ContractTransactionResponse extends provider_js_1.TransactionResponse {
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
exports.ContractTransactionResponse = ContractTransactionResponse;
/**
 *  A **ContractUnknownEventPayload** is included as the last parameter to
 *  Contract Events when the event does not match any events in the ABI.
 */
class ContractUnknownEventPayload extends index_js_1.EventPayload {
    /**
     *  The log with no matching events.
     */
    log;
    /**
     *  @_event:
     */
    constructor(contract, listener, filter, log) {
        super(contract, listener, filter);
        (0, index_js_1.defineProperties)(this, { log });
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
exports.ContractUnknownEventPayload = ContractUnknownEventPayload;
/**
 *  A **ContractEventPayload** is included as the last parameter to
 *  Contract Events when the event is known.
 */
class ContractEventPayload extends ContractUnknownEventPayload {
    /**
     *  @_ignore:
     */
    constructor(contract, listener, filter, fragment, _log) {
        super(contract, listener, filter, new EventLog(_log, contract.interface, fragment));
        const args = contract.interface.decodeEventLog(fragment, this.log.data, this.log.topics);
        (0, index_js_1.defineProperties)(this, { args, fragment });
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
exports.ContractEventPayload = ContractEventPayload;
//# sourceMappingURL=wrappers.js.map