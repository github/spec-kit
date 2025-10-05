"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BrowserProvider = void 0;
const index_js_1 = require("../utils/index.js");
const provider_jsonrpc_js_1 = require("./provider-jsonrpc.js");
;
/**
 *  A **BrowserProvider** is intended to wrap an injected provider which
 *  adheres to the [[link-eip-1193]] standard, which most (if not all)
 *  currently do.
 */
class BrowserProvider extends provider_jsonrpc_js_1.JsonRpcApiPollingProvider {
    #request;
    #providerInfo;
    /**
     *  Connect to the %%ethereum%% provider, optionally forcing the
     *  %%network%%.
     */
    constructor(ethereum, network, _options) {
        // Copy the options
        const options = Object.assign({}, ((_options != null) ? _options : {}), { batchMaxCount: 1 });
        (0, index_js_1.assertArgument)(ethereum && ethereum.request, "invalid EIP-1193 provider", "ethereum", ethereum);
        super(network, options);
        this.#providerInfo = null;
        if (_options && _options.providerInfo) {
            this.#providerInfo = _options.providerInfo;
        }
        this.#request = async (method, params) => {
            const payload = { method, params };
            this.emit("debug", { action: "sendEip1193Request", payload });
            try {
                const result = await ethereum.request(payload);
                this.emit("debug", { action: "receiveEip1193Result", result });
                return result;
            }
            catch (e) {
                const error = new Error(e.message);
                error.code = e.code;
                error.data = e.data;
                error.payload = payload;
                this.emit("debug", { action: "receiveEip1193Error", error });
                throw error;
            }
        };
    }
    get providerInfo() {
        return this.#providerInfo;
    }
    async send(method, params) {
        await this._start();
        return await super.send(method, params);
    }
    async _send(payload) {
        (0, index_js_1.assertArgument)(!Array.isArray(payload), "EIP-1193 does not support batch request", "payload", payload);
        try {
            const result = await this.#request(payload.method, payload.params || []);
            return [{ id: payload.id, result }];
        }
        catch (e) {
            return [{
                    id: payload.id,
                    error: { code: e.code, data: e.data, message: e.message }
                }];
        }
    }
    getRpcError(payload, error) {
        error = JSON.parse(JSON.stringify(error));
        // EIP-1193 gives us some machine-readable error codes, so rewrite
        // them into Ethers standard errors.
        switch (error.error.code || -1) {
            case 4001:
                error.error.message = `ethers-user-denied: ${error.error.message}`;
                break;
            case 4200:
                error.error.message = `ethers-unsupported: ${error.error.message}`;
                break;
        }
        return super.getRpcError(payload, error);
    }
    /**
     *  Resolves to ``true`` if the provider manages the %%address%%.
     */
    async hasSigner(address) {
        if (address == null) {
            address = 0;
        }
        const accounts = await this.send("eth_accounts", []);
        if (typeof (address) === "number") {
            return (accounts.length > address);
        }
        address = address.toLowerCase();
        return accounts.filter((a) => (a.toLowerCase() === address)).length !== 0;
    }
    async getSigner(address) {
        if (address == null) {
            address = 0;
        }
        if (!(await this.hasSigner(address))) {
            try {
                await this.#request("eth_requestAccounts", []);
            }
            catch (error) {
                const payload = error.payload;
                throw this.getRpcError(payload, { id: payload.id, error });
            }
        }
        return await super.getSigner(address);
    }
    /**
     *  Discover and connect to a Provider in the Browser using the
     *  [[link-eip-6963]] discovery mechanism. If no providers are
     *  present, ``null`` is resolved.
     */
    static async discover(options) {
        if (options == null) {
            options = {};
        }
        if (options.provider) {
            return new BrowserProvider(options.provider);
        }
        const context = options.window ? options.window :
            (typeof (window) !== "undefined") ? window : null;
        if (context == null) {
            return null;
        }
        const anyProvider = options.anyProvider;
        if (anyProvider && context.ethereum) {
            return new BrowserProvider(context.ethereum);
        }
        if (!("addEventListener" in context && "dispatchEvent" in context
            && "removeEventListener" in context)) {
            return null;
        }
        const timeout = options.timeout ? options.timeout : 300;
        if (timeout === 0) {
            return null;
        }
        return await (new Promise((resolve, reject) => {
            let found = [];
            const addProvider = (event) => {
                found.push(event.detail);
                if (anyProvider) {
                    finalize();
                }
            };
            const finalize = () => {
                clearTimeout(timer);
                if (found.length) {
                    // If filtering is provided:
                    if (options && options.filter) {
                        // Call filter, with a copies of found provider infos
                        const filtered = options.filter(found.map(i => Object.assign({}, (i.info))));
                        if (filtered == null) {
                            // No provider selected
                            resolve(null);
                        }
                        else if (filtered instanceof BrowserProvider) {
                            // Custom provider created
                            resolve(filtered);
                        }
                        else {
                            // Find the matching provider
                            let match = null;
                            if (filtered.uuid) {
                                const matches = found.filter(f => (filtered.uuid === f.info.uuid));
                                // @TODO: What should happen if multiple values
                                //        for the same UUID?
                                match = matches[0];
                            }
                            if (match) {
                                const { provider, info } = match;
                                resolve(new BrowserProvider(provider, undefined, {
                                    providerInfo: info
                                }));
                            }
                            else {
                                reject((0, index_js_1.makeError)("filter returned unknown info", "UNSUPPORTED_OPERATION", {
                                    value: filtered
                                }));
                            }
                        }
                    }
                    else {
                        // Pick the first found provider
                        const { provider, info } = found[0];
                        resolve(new BrowserProvider(provider, undefined, {
                            providerInfo: info
                        }));
                    }
                }
                else {
                    // Nothing found
                    resolve(null);
                }
                context.removeEventListener("eip6963:announceProvider", addProvider);
            };
            const timer = setTimeout(() => { finalize(); }, timeout);
            context.addEventListener("eip6963:announceProvider", addProvider);
            context.dispatchEvent(new Event("eip6963:requestProvider"));
        }));
    }
}
exports.BrowserProvider = BrowserProvider;
//# sourceMappingURL=provider-browser.js.map