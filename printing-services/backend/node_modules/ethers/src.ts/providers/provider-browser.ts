
import { assertArgument, makeError } from "../utils/index.js";

import { JsonRpcApiPollingProvider } from "./provider-jsonrpc.js";

import type {
    JsonRpcApiProviderOptions,
    JsonRpcError, JsonRpcPayload, JsonRpcResult,
    JsonRpcSigner
} from "./provider-jsonrpc.js";
import type { Network, Networkish } from "./network.js";

/**
 *  The interface to an [[link-eip-1193]] provider, which is a standard
 *  used by most injected providers, which the [[BrowserProvider]] accepts
 *  and exposes the API of.
 */
export interface Eip1193Provider {
    /**
     *  See [[link-eip-1193]] for details on this method.
     */
    request(request: { method: string, params?: Array<any> | Record<string, any> }): Promise<any>;
};

/**
 *  The possible additional events dispatched when using the ``"debug"``
 *  event on a [[BrowserProvider]].
 */
export type DebugEventBrowserProvider = {
    action: "sendEip1193Payload",
    payload: { method: string, params: Array<any> }
} | {
    action: "receiveEip1193Result",
    result: any
} | {
    action: "receiveEip1193Error",
    error: Error
};

/**
 *  Provider info provided by the [[link-eip-6963]] discovery mechanism.
 */
export interface Eip6963ProviderInfo {
    uuid: string;
    name: string;
    icon: string;
    rdns: string;
}

interface Eip6963ProviderDetail {
    info: Eip6963ProviderInfo;
    provider: Eip1193Provider;
}

interface Eip6963Announcement {
    type: "eip6963:announceProvider";
    detail: Eip6963ProviderDetail
}

export type BrowserProviderOptions = {
    polling?: boolean;
    staticNetwork?: null | boolean | Network;

    cacheTimeout?: number;
    pollingInterval?: number;

    providerInfo?: Eip6963ProviderInfo;
};

/**
 *  Specifies how [[link-eip-6963]] discovery should proceed.
 *
 *  See: [[BrowserProvider-discover]]
 */
export interface BrowserDiscoverOptions {
    /**
     *  Override provider detection with this provider.
     */
    provider?: Eip1193Provider;

    /**
     *  Duration to wait to detect providers. (default: 300ms)
     */
    timeout?: number;

    /**
     *  Return the first detected provider. Otherwise wait for %%timeout%%
     *  and allowing filtering before selecting the desired provider.
     */
    anyProvider?: boolean;

    /**
     *  Use the provided window context. Useful in non-standard
     *  environments or to hijack where a provider comes from.
     */
    window?: any;

    /**
     *  Explicitly choose which provider to used once scanning is complete.
     */
    filter?: (found: Array<Eip6963ProviderInfo>) => null | BrowserProvider |
      Eip6963ProviderInfo;
}


/**
 *  A **BrowserProvider** is intended to wrap an injected provider which
 *  adheres to the [[link-eip-1193]] standard, which most (if not all)
 *  currently do.
 */
export class BrowserProvider extends JsonRpcApiPollingProvider {
    #request: (method: string, params: Array<any> | Record<string, any>) => Promise<any>;

    #providerInfo: null | Eip6963ProviderInfo;

    /**
     *  Connect to the %%ethereum%% provider, optionally forcing the
     *  %%network%%.
     */
    constructor(ethereum: Eip1193Provider, network?: Networkish, _options?: BrowserProviderOptions) {

        // Copy the options
        const options: JsonRpcApiProviderOptions = Object.assign({ },
          ((_options != null) ? _options: { }),
          { batchMaxCount: 1 });

        assertArgument(ethereum && ethereum.request, "invalid EIP-1193 provider", "ethereum", ethereum);

        super(network, options);

        this.#providerInfo = null;
        if (_options && _options.providerInfo) {
            this.#providerInfo = _options.providerInfo;
        }

        this.#request = async (method: string, params: Array<any> | Record<string, any>) => {
            const payload = { method, params };
            this.emit("debug", { action: "sendEip1193Request", payload });
            try {
                const result = await ethereum.request(payload);
                this.emit("debug", { action: "receiveEip1193Result", result });
                return result;
            } catch (e: any) {
                const error = new Error(e.message);
                (<any>error).code = e.code;
                (<any>error).data = e.data;
                (<any>error).payload = payload;
                this.emit("debug", { action: "receiveEip1193Error", error });
                throw error;
            }
        };
    }

    get providerInfo(): null | Eip6963ProviderInfo {
        return this.#providerInfo;
    }

    async send(method: string, params: Array<any> | Record<string, any>): Promise<any> {
        await this._start();

        return await super.send(method, params);
    }

    async _send(payload: JsonRpcPayload | Array<JsonRpcPayload>): Promise<Array<JsonRpcResult | JsonRpcError>> {
        assertArgument(!Array.isArray(payload), "EIP-1193 does not support batch request", "payload", payload);

        try {
            const result = await this.#request(payload.method, payload.params || [ ]);
            return [ { id: payload.id, result } ];
        } catch (e: any) {
            return [ {
                id: payload.id,
                error: { code: e.code, data: e.data, message: e.message }
            } ];
        }
    }

    getRpcError(payload: JsonRpcPayload, error: JsonRpcError): Error {

        error = JSON.parse(JSON.stringify(error));

        // EIP-1193 gives us some machine-readable error codes, so rewrite
        // them into Ethers standard errors.
        switch (error.error.code || -1) {
            case 4001:
                error.error.message = `ethers-user-denied: ${ error.error.message }`;
                break;
            case 4200:
                error.error.message = `ethers-unsupported: ${ error.error.message }`;
                break;
        }

        return super.getRpcError(payload, error);
    }

    /**
     *  Resolves to ``true`` if the provider manages the %%address%%.
     */
    async hasSigner(address: number | string): Promise<boolean> {
        if (address == null) { address = 0; }

        const accounts = await this.send("eth_accounts", [ ]);
        if (typeof(address) === "number") {
            return (accounts.length > address);
        }

        address = address.toLowerCase();
        return accounts.filter((a: string) => (a.toLowerCase() === address)).length !== 0;
    }

    async getSigner(address?: number | string): Promise<JsonRpcSigner> {
        if (address == null) { address = 0; }

        if (!(await this.hasSigner(address))) {
            try {
                await this.#request("eth_requestAccounts", [ ]);

            } catch (error: any) {
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
    static async discover(options?: BrowserDiscoverOptions): Promise<null | BrowserProvider> {
        if (options == null) { options = { }; }

        if (options.provider) {
            return new BrowserProvider(options.provider);
        }

        const context = options.window ? options.window:
            (typeof(window) !== "undefined") ? window: null;

        if (context == null) { return null; }

        const anyProvider = options.anyProvider;
        if (anyProvider && context.ethereum) {
            return new BrowserProvider(context.ethereum);
        }

        if (!("addEventListener" in context && "dispatchEvent" in context
          && "removeEventListener" in context)) {
            return null;
        }

        const timeout = options.timeout ? options.timeout: 300;
        if (timeout === 0) { return null; }

        return await (new Promise((resolve, reject) => {
            let found: Array<Eip6963ProviderDetail> = [ ];

            const addProvider = (event: Eip6963Announcement) => {
                found.push(event.detail);
                if (anyProvider) { finalize(); }
            };

            const finalize = () => {
                clearTimeout(timer);

                if (found.length) {

                    // If filtering is provided:
                    if (options && options.filter) {

                        // Call filter, with a copies of found provider infos
                        const filtered = options.filter(found.map(i =>
                          Object.assign({ }, (i.info))));

                        if (filtered == null) {
                            // No provider selected
                            resolve(null);

                        } else if (filtered instanceof BrowserProvider) {
                            // Custom provider created
                            resolve(filtered);

                        } else {
                            // Find the matching provider
                            let match: null | Eip6963ProviderDetail = null;
                            if (filtered.uuid) {
                                const matches = found.filter(f =>
                                  (filtered.uuid === f.info.uuid));
                                // @TODO: What should happen if multiple values
                                //        for the same UUID?
                                match = matches[0];
                            }

                            if (match) {
                                const { provider, info } = match;
                                resolve(new BrowserProvider(provider, undefined, {
                                    providerInfo: info
                                }));
                            } else {
                                reject(makeError("filter returned unknown info", "UNSUPPORTED_OPERATION", {
                                    value: filtered
                                }));
                            }
                        }

                    } else {

                        // Pick the first found provider
                        const { provider, info } = found[0];
                        resolve(new BrowserProvider(provider, undefined, {
                            providerInfo: info
                        }));
                    }

                } else {
                    // Nothing found
                    resolve(null);
                }

                context.removeEventListener(<any>"eip6963:announceProvider",
                  addProvider);
            };

            const timer = setTimeout(() => { finalize(); }, timeout);

            context.addEventListener(<any>"eip6963:announceProvider",
              addProvider);

            context.dispatchEvent(new Event("eip6963:requestProvider"));
        }));
    }
}
