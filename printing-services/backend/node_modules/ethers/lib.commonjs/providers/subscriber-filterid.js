"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FilterIdPendingSubscriber = exports.FilterIdEventSubscriber = exports.FilterIdSubscriber = void 0;
const index_js_1 = require("../utils/index.js");
const subscriber_polling_js_1 = require("./subscriber-polling.js");
function copy(obj) {
    return JSON.parse(JSON.stringify(obj));
}
/**
 *  Some backends support subscribing to events using a Filter ID.
 *
 *  When subscribing with this technique, the node issues a unique
 *  //Filter ID//. At this point the node dedicates resources to
 *  the filter, so that periodic calls to follow up on the //Filter ID//
 *  will receive any events since the last call.
 *
 *  @_docloc: api/providers/abstract-provider
 */
class FilterIdSubscriber {
    #provider;
    #filterIdPromise;
    #poller;
    #running;
    #network;
    #hault;
    /**
     *  Creates a new **FilterIdSubscriber** which will used [[_subscribe]]
     *  and [[_emitResults]] to setup the subscription and provide the event
     *  to the %%provider%%.
     */
    constructor(provider) {
        this.#provider = provider;
        this.#filterIdPromise = null;
        this.#poller = this.#poll.bind(this);
        this.#running = false;
        this.#network = null;
        this.#hault = false;
    }
    /**
     *  Sub-classes **must** override this to begin the subscription.
     */
    _subscribe(provider) {
        throw new Error("subclasses must override this");
    }
    /**
     *  Sub-classes **must** override this handle the events.
     */
    _emitResults(provider, result) {
        throw new Error("subclasses must override this");
    }
    /**
     *  Sub-classes **must** override this handle recovery on errors.
     */
    _recover(provider) {
        throw new Error("subclasses must override this");
    }
    async #poll(blockNumber) {
        try {
            // Subscribe if necessary
            if (this.#filterIdPromise == null) {
                this.#filterIdPromise = this._subscribe(this.#provider);
            }
            // Get the Filter ID
            let filterId = null;
            try {
                filterId = await this.#filterIdPromise;
            }
            catch (error) {
                if (!(0, index_js_1.isError)(error, "UNSUPPORTED_OPERATION") || error.operation !== "eth_newFilter") {
                    throw error;
                }
            }
            // The backend does not support Filter ID; downgrade to
            // polling
            if (filterId == null) {
                this.#filterIdPromise = null;
                this.#provider._recoverSubscriber(this, this._recover(this.#provider));
                return;
            }
            const network = await this.#provider.getNetwork();
            if (!this.#network) {
                this.#network = network;
            }
            if (this.#network.chainId !== network.chainId) {
                throw new Error("chaid changed");
            }
            if (this.#hault) {
                return;
            }
            const result = await this.#provider.send("eth_getFilterChanges", [filterId]);
            await this._emitResults(this.#provider, result);
        }
        catch (error) {
            console.log("@TODO", error);
        }
        this.#provider.once("block", this.#poller);
    }
    #teardown() {
        const filterIdPromise = this.#filterIdPromise;
        if (filterIdPromise) {
            this.#filterIdPromise = null;
            filterIdPromise.then((filterId) => {
                if (this.#provider.destroyed) {
                    return;
                }
                this.#provider.send("eth_uninstallFilter", [filterId]);
            });
        }
    }
    start() {
        if (this.#running) {
            return;
        }
        this.#running = true;
        this.#poll(-2);
    }
    stop() {
        if (!this.#running) {
            return;
        }
        this.#running = false;
        this.#hault = true;
        this.#teardown();
        this.#provider.off("block", this.#poller);
    }
    pause(dropWhilePaused) {
        if (dropWhilePaused) {
            this.#teardown();
        }
        this.#provider.off("block", this.#poller);
    }
    resume() { this.start(); }
}
exports.FilterIdSubscriber = FilterIdSubscriber;
/**
 *  A **FilterIdSubscriber** for receiving contract events.
 *
 *  @_docloc: api/providers/abstract-provider
 */
class FilterIdEventSubscriber extends FilterIdSubscriber {
    #event;
    /**
     *  Creates a new **FilterIdEventSubscriber** attached to %%provider%%
     *  listening for %%filter%%.
     */
    constructor(provider, filter) {
        super(provider);
        this.#event = copy(filter);
    }
    _recover(provider) {
        return new subscriber_polling_js_1.PollingEventSubscriber(provider, this.#event);
    }
    async _subscribe(provider) {
        const filterId = await provider.send("eth_newFilter", [this.#event]);
        return filterId;
    }
    async _emitResults(provider, results) {
        for (const result of results) {
            provider.emit(this.#event, provider._wrapLog(result, provider._network));
        }
    }
}
exports.FilterIdEventSubscriber = FilterIdEventSubscriber;
/**
 *  A **FilterIdSubscriber** for receiving pending transactions events.
 *
 *  @_docloc: api/providers/abstract-provider
 */
class FilterIdPendingSubscriber extends FilterIdSubscriber {
    async _subscribe(provider) {
        return await provider.send("eth_newPendingTransactionFilter", []);
    }
    async _emitResults(provider, results) {
        for (const result of results) {
            provider.emit("pending", result);
        }
    }
}
exports.FilterIdPendingSubscriber = FilterIdPendingSubscriber;
//# sourceMappingURL=subscriber-filterid.js.map