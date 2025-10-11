import { JsonRpcApiPollingProvider } from "./provider-jsonrpc.js";
import type { JsonRpcError, JsonRpcPayload, JsonRpcResult, JsonRpcSigner } from "./provider-jsonrpc.js";
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
    request(request: {
        method: string;
        params?: Array<any> | Record<string, any>;
    }): Promise<any>;
}
/**
 *  The possible additional events dispatched when using the ``"debug"``
 *  event on a [[BrowserProvider]].
 */
export type DebugEventBrowserProvider = {
    action: "sendEip1193Payload";
    payload: {
        method: string;
        params: Array<any>;
    };
} | {
    action: "receiveEip1193Result";
    result: any;
} | {
    action: "receiveEip1193Error";
    error: Error;
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
    filter?: (found: Array<Eip6963ProviderInfo>) => null | BrowserProvider | Eip6963ProviderInfo;
}
/**
 *  A **BrowserProvider** is intended to wrap an injected provider which
 *  adheres to the [[link-eip-1193]] standard, which most (if not all)
 *  currently do.
 */
export declare class BrowserProvider extends JsonRpcApiPollingProvider {
    #private;
    /**
     *  Connect to the %%ethereum%% provider, optionally forcing the
     *  %%network%%.
     */
    constructor(ethereum: Eip1193Provider, network?: Networkish, _options?: BrowserProviderOptions);
    get providerInfo(): null | Eip6963ProviderInfo;
    send(method: string, params: Array<any> | Record<string, any>): Promise<any>;
    _send(payload: JsonRpcPayload | Array<JsonRpcPayload>): Promise<Array<JsonRpcResult | JsonRpcError>>;
    getRpcError(payload: JsonRpcPayload, error: JsonRpcError): Error;
    /**
     *  Resolves to ``true`` if the provider manages the %%address%%.
     */
    hasSigner(address: number | string): Promise<boolean>;
    getSigner(address?: number | string): Promise<JsonRpcSigner>;
    /**
     *  Discover and connect to a Provider in the Browser using the
     *  [[link-eip-6963]] discovery mechanism. If no providers are
     *  present, ``null`` is resolved.
     */
    static discover(options?: BrowserDiscoverOptions): Promise<null | BrowserProvider>;
}
//# sourceMappingURL=provider-browser.d.ts.map