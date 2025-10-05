"use strict";
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.SocketProvider = exports.SocketEventSubscriber = exports.SocketPendingSubscriber = exports.SocketBlockSubscriber = exports.SocketSubscriber = void 0;
const abstract_provider_js_1 = require("./abstract-provider.js");
const index_js_1 = require("../utils/index.js");
const provider_jsonrpc_js_1 = require("./provider-jsonrpc.js");
/**
 *  A **SocketSubscriber** uses a socket transport to handle events and
 *  should use [[_emit]] to manage the events.
 */
class SocketSubscriber {
    #provider;
    #filter;
    /**
     *  The filter.
     */
    get filter() { return JSON.parse(this.#filter); }
    #filterId;
    #paused;
    #emitPromise;
    /**
     *  Creates a new **SocketSubscriber** attached to %%provider%% listening
     *  to %%filter%%.
     */
    constructor(provider, filter) {
        this.#provider = provider;
        this.#filter = JSON.stringify(filter);
        this.#filterId = null;
        this.#paused = null;
        this.#emitPromise = null;
    }
    start() {
        this.#filterId = this.#provider.send("eth_subscribe", this.filter).then((filterId) => {
            ;
            this.#provider._register(filterId, this);
            return filterId;
        });
    }
    stop() {
        (this.#filterId).then((filterId) => {
            if (this.#provider.destroyed) {
                return;
            }
            this.#provider.send("eth_unsubscribe", [filterId]);
        });
        this.#filterId = null;
    }
    // @TODO: pause should trap the current blockNumber, unsub, and on resume use getLogs
    //        and resume
    pause(dropWhilePaused) {
        (0, index_js_1.assert)(dropWhilePaused, "preserve logs while paused not supported by SocketSubscriber yet", "UNSUPPORTED_OPERATION", { operation: "pause(false)" });
        this.#paused = !!dropWhilePaused;
    }
    resume() {
        this.#paused = null;
    }
    /**
     *  @_ignore:
     */
    _handleMessage(message) {
        if (this.#filterId == null) {
            return;
        }
        if (this.#paused === null) {
            let emitPromise = this.#emitPromise;
            if (emitPromise == null) {
                emitPromise = this._emit(this.#provider, message);
            }
            else {
                emitPromise = emitPromise.then(async () => {
                    await this._emit(this.#provider, message);
                });
            }
            this.#emitPromise = emitPromise.then(() => {
                if (this.#emitPromise === emitPromise) {
                    this.#emitPromise = null;
                }
            });
        }
    }
    /**
     *  Sub-classes **must** override this to emit the events on the
     *  provider.
     */
    async _emit(provider, message) {
        throw new Error("sub-classes must implemente this; _emit");
    }
}
exports.SocketSubscriber = SocketSubscriber;
/**
 *  A **SocketBlockSubscriber** listens for ``newHeads`` events and emits
 *  ``"block"`` events.
 */
class SocketBlockSubscriber extends SocketSubscriber {
    /**
     *  @_ignore:
     */
    constructor(provider) {
        super(provider, ["newHeads"]);
    }
    async _emit(provider, message) {
        provider.emit("block", parseInt(message.number));
    }
}
exports.SocketBlockSubscriber = SocketBlockSubscriber;
/**
 *  A **SocketPendingSubscriber** listens for pending transacitons and emits
 *  ``"pending"`` events.
 */
class SocketPendingSubscriber extends SocketSubscriber {
    /**
     *  @_ignore:
     */
    constructor(provider) {
        super(provider, ["newPendingTransactions"]);
    }
    async _emit(provider, message) {
        provider.emit("pending", message);
    }
}
exports.SocketPendingSubscriber = SocketPendingSubscriber;
/**
 *  A **SocketEventSubscriber** listens for event logs.
 */
class SocketEventSubscriber extends SocketSubscriber {
    #logFilter;
    /**
     *  The filter.
     */
    get logFilter() { return JSON.parse(this.#logFilter); }
    /**
     *  @_ignore:
     */
    constructor(provider, filter) {
        super(provider, ["logs", filter]);
        this.#logFilter = JSON.stringify(filter);
    }
    async _emit(provider, message) {
        provider.emit(this.logFilter, provider._wrapLog(message, provider._network));
    }
}
exports.SocketEventSubscriber = SocketEventSubscriber;
/**
 *  A **SocketProvider** is backed by a long-lived connection over a
 *  socket, which can subscribe and receive real-time messages over
 *  its communication channel.
 */
class SocketProvider extends provider_jsonrpc_js_1.JsonRpcApiProvider {
    #callbacks;
    // Maps each filterId to its subscriber
    #subs;
    // If any events come in before a subscriber has finished
    // registering, queue them
    #pending;
    /**
     *  Creates a new **SocketProvider** connected to %%network%%.
     *
     *  If unspecified, the network will be discovered.
     */
    constructor(network, _options) {
        // Copy the options
        const options = Object.assign({}, (_options != null) ? _options : {});
        // Support for batches is generally not supported for
        // connection-base providers; if this changes in the future
        // the _send should be updated to reflect this
        (0, index_js_1.assertArgument)(options.batchMaxCount == null || options.batchMaxCount === 1, "sockets-based providers do not support batches", "options.batchMaxCount", _options);
        options.batchMaxCount = 1;
        // Socket-based Providers (generally) cannot change their network,
        // since they have a long-lived connection; but let people override
        // this if they have just cause.
        if (options.staticNetwork == null) {
            options.staticNetwork = true;
        }
        super(network, options);
        this.#callbacks = new Map();
        this.#subs = new Map();
        this.#pending = new Map();
    }
    // This value is only valid after _start has been called
    /*
    get _network(): Network {
        if (this.#network == null) {
            throw new Error("this shouldn't happen");
        }
        return this.#network.clone();
    }
    */
    _getSubscriber(sub) {
        switch (sub.type) {
            case "close":
                return new abstract_provider_js_1.UnmanagedSubscriber("close");
            case "block":
                return new SocketBlockSubscriber(this);
            case "pending":
                return new SocketPendingSubscriber(this);
            case "event":
                return new SocketEventSubscriber(this, sub.filter);
            case "orphan":
                // Handled auto-matically within AbstractProvider
                // when the log.removed = true
                if (sub.filter.orphan === "drop-log") {
                    return new abstract_provider_js_1.UnmanagedSubscriber("drop-log");
                }
        }
        return super._getSubscriber(sub);
    }
    /**
     *  Register a new subscriber. This is used internalled by Subscribers
     *  and generally is unecessary unless extending capabilities.
     */
    _register(filterId, subscriber) {
        this.#subs.set(filterId, subscriber);
        const pending = this.#pending.get(filterId);
        if (pending) {
            for (const message of pending) {
                subscriber._handleMessage(message);
            }
            this.#pending.delete(filterId);
        }
    }
    async _send(payload) {
        // WebSocket provider doesn't accept batches
        (0, index_js_1.assertArgument)(!Array.isArray(payload), "WebSocket does not support batch send", "payload", payload);
        // @TODO: stringify payloads here and store to prevent mutations
        // Prepare a promise to respond to
        const promise = new Promise((resolve, reject) => {
            this.#callbacks.set(payload.id, { payload, resolve, reject });
        });
        // Wait until the socket is connected before writing to it
        await this._waitUntilReady();
        // Write the request to the socket
        await this._write(JSON.stringify(payload));
        return [await promise];
    }
    // Sub-classes must call this once they are connected
    /*
    async _start(): Promise<void> {
        if (this.#ready) { return; }

        for (const { payload } of this.#callbacks.values()) {
            await this._write(JSON.stringify(payload));
        }

        this.#ready = (async function() {
            await super._start();
        })();
    }
    */
    /**
     *  Sub-classes **must** call this with messages received over their
     *  transport to be processed and dispatched.
     */
    async _processMessage(message) {
        const result = (JSON.parse(message));
        if (result && typeof (result) === "object" && "id" in result) {
            const callback = this.#callbacks.get(result.id);
            if (callback == null) {
                this.emit("error", (0, index_js_1.makeError)("received result for unknown id", "UNKNOWN_ERROR", {
                    reasonCode: "UNKNOWN_ID",
                    result
                }));
                return;
            }
            this.#callbacks.delete(result.id);
            callback.resolve(result);
        }
        else if (result && result.method === "eth_subscription") {
            const filterId = result.params.subscription;
            const subscriber = this.#subs.get(filterId);
            if (subscriber) {
                subscriber._handleMessage(result.params.result);
            }
            else {
                let pending = this.#pending.get(filterId);
                if (pending == null) {
                    pending = [];
                    this.#pending.set(filterId, pending);
                }
                pending.push(result.params.result);
            }
        }
        else {
            this.emit("error", (0, index_js_1.makeError)("received unexpected message", "UNKNOWN_ERROR", {
                reasonCode: "UNEXPECTED_MESSAGE",
                result
            }));
            return;
        }
    }
    /**
     *  Sub-classes **must** override this to send %%message%% over their
     *  transport.
     */
    async _write(message) {
        throw new Error("sub-classes must override this");
    }
}
exports.SocketProvider = SocketProvider;
//# sourceMappingURL=provider-socket.js.map