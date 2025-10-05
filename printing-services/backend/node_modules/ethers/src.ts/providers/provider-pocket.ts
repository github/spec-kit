/**
 *  [[link-pocket]] provides a third-party service for connecting to
 *  various blockchains over JSON-RPC.
 *
 *  **Supported Networks**
 *
 *  - Ethereum Mainnet (``mainnet``)
 *  - Goerli Testnet (``goerli``)
 *  - Polygon (``matic``)
 *  - Arbitrum (``arbitrum``)
 *
 *  @_subsection: api/providers/thirdparty:Pocket  [providers-pocket]
 */
import {
    defineProperties, FetchRequest, assertArgument
} from "../utils/index.js";

import { AbstractProvider } from "./abstract-provider.js";
import { showThrottleMessage } from "./community.js";
import { Network } from "./network.js";
import { JsonRpcProvider } from "./provider-jsonrpc.js";

import type { CommunityResourcable } from "./community.js";
import type { Networkish } from "./network.js";

const defaultApplicationId = "62e1ad51b37b8e00394bda3b";

function getHost(name: string): string {
    switch (name) {
        case "mainnet":
            return  "eth-mainnet.gateway.pokt.network";
        case "goerli":
            return "eth-goerli.gateway.pokt.network";

        case "matic":
            return "poly-mainnet.gateway.pokt.network";
        case "matic-mumbai":
            return "polygon-mumbai-rpc.gateway.pokt.network";
    }

    assertArgument(false, "unsupported network", "network", name);
}


/**
 *  The **PocketProvider** connects to the [[link-pocket]]
 *  JSON-RPC end-points.
 *
 *  By default, a highly-throttled API key is used, which is
 *  appropriate for quick prototypes and simple scripts. To
 *  gain access to an increased rate-limit, it is highly
 *  recommended to [sign up here](link-pocket-signup).
 */
export class PocketProvider extends JsonRpcProvider implements CommunityResourcable {

    /**
     *  The Application ID for the Pocket connection.
     */
    readonly applicationId!: string;

    /**
     *  The Application Secret for making authenticated requests
     *  to the Pocket connection.
     */
    readonly applicationSecret!: null | string;

    /**
     *  Create a new **PocketProvider**.
     *
     *  By default connecting to ``mainnet`` with a highly throttled
     *  API key.
     */
    constructor(_network?: Networkish, applicationId?: null | string, applicationSecret?: null | string) {
        if (_network == null) { _network = "mainnet"; }
        const network = Network.from(_network);
        if (applicationId == null) { applicationId = defaultApplicationId; }
        if (applicationSecret == null) { applicationSecret = null; }

        const options = { staticNetwork: network };

        const request = PocketProvider.getRequest(network, applicationId, applicationSecret);
        super(request, network, options);

        defineProperties<PocketProvider>(this, { applicationId, applicationSecret });
    }

    _getProvider(chainId: number): AbstractProvider {
        try {
            return new PocketProvider(chainId, this.applicationId, this.applicationSecret);
        } catch (error) { }
        return super._getProvider(chainId);
    }

    /**
     *  Returns a prepared request for connecting to %%network%% with
     *  %%applicationId%%.
     */
    static getRequest(network: Network, applicationId?: null | string, applicationSecret?: null | string): FetchRequest {
        if (applicationId == null) { applicationId = defaultApplicationId; }

        const request = new FetchRequest(`https:/\/${ getHost(network.name) }/v1/lb/${ applicationId }`);
        request.allowGzip = true;

        if (applicationSecret) {
            request.setCredentials("", applicationSecret);
        }

        if (applicationId === defaultApplicationId) {
            request.retryFunc = async (request, response, attempt) => {
                showThrottleMessage("PocketProvider");
                return true;
            };
        }

        return request;
    }

    isCommunityResource(): boolean {
        return (this.applicationId === defaultApplicationId);
    }
}
