/**
 *  [[link-chainstack]] provides a third-party service for connecting to
 *  various blockchains over JSON-RPC.
 *
 *  **Supported Networks**
 *
 *  - Ethereum Mainnet (``mainnet``)
 *  - Arbitrum (``arbitrum``)
 *  - BNB Smart Chain Mainnet (``bnb``)
 *  - Polygon (``matic``)
 *
 *  @_subsection: api/providers/thirdparty:Chainstack  [providers-chainstack]
 */
import {
    defineProperties, FetchRequest, assertArgument
} from "../utils/index.js";

import { showThrottleMessage } from "./community.js";
import { Network } from "./network.js";
import { JsonRpcProvider } from "./provider-jsonrpc.js";

import type { AbstractProvider } from "./abstract-provider.js";
import type { CommunityResourcable } from "./community.js";
import type { Networkish } from "./network.js";


function getApiKey(name: string): string {
    switch (name) {
        case "mainnet": return "39f1d67cedf8b7831010a665328c9197";
        case "arbitrum": return "0550c209db33c3abf4cc927e1e18cea1"
        case "bnb": return "98b5a77e531614387366f6fc5da097f8";
        case "matic": return "cd9d4d70377471aa7c142ec4a4205249";
    }

    assertArgument(false, "unsupported network", "network", name);
}

function getHost(name: string): string {
    switch(name) {
        case "mainnet":
            return "ethereum-mainnet.core.chainstack.com";
        case "arbitrum":
            return "arbitrum-mainnet.core.chainstack.com";
        case "bnb":
            return "bsc-mainnet.core.chainstack.com";
        case "matic":
            return "polygon-mainnet.core.chainstack.com";
    }

    assertArgument(false, "unsupported network", "network", name);
}

/**
 *  The **ChainstackProvider** connects to the [[link-chainstack]]
 *  JSON-RPC end-points.
 *
 *  By default, a highly-throttled API key is used, which is
 *  appropriate for quick prototypes and simple scripts. To
 *  gain access to an increased rate-limit, it is highly
 *  recommended to [sign up here](link-chainstack).
 */
export class ChainstackProvider extends JsonRpcProvider implements CommunityResourcable {
    /**
     *  The API key for the Chainstack connection.
     */
    readonly apiKey!: string;

    /**
     *  Creates a new **ChainstackProvider**.
     */
    constructor(_network?: Networkish, apiKey?: null | string) {
        if (_network == null) { _network = "mainnet"; }
        const network = Network.from(_network);

        if (apiKey == null) { apiKey = getApiKey(network.name); }

        const request = ChainstackProvider.getRequest(network, apiKey);
        super(request, network, { staticNetwork: network });

        defineProperties<ChainstackProvider>(this, { apiKey });
    }

    _getProvider(chainId: number): AbstractProvider {
        try {
            return new ChainstackProvider(chainId, this.apiKey);
        } catch (error) { }
        return super._getProvider(chainId);
    }

    isCommunityResource(): boolean {
        return (this.apiKey === getApiKey(this._network.name));
    }

    /**
     *  Returns a prepared request for connecting to %%network%%
     *  with %%apiKey%% and %%projectSecret%%.
     */
    static getRequest(network: Network, apiKey?: null | string): FetchRequest {
        if (apiKey == null) { apiKey = getApiKey(network.name); }

        const request = new FetchRequest(`https:/\/${ getHost(network.name) }/${ apiKey }`);
        request.allowGzip = true;

        if (apiKey === getApiKey(network.name)) {
            request.retryFunc = async (request, response, attempt) => {
                showThrottleMessage("ChainstackProvider");
                return true;
            };
        }

        return request;
    }
}
