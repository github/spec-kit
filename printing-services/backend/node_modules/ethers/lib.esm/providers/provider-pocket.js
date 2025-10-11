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
import { defineProperties, FetchRequest, assertArgument } from "../utils/index.js";
import { showThrottleMessage } from "./community.js";
import { Network } from "./network.js";
import { JsonRpcProvider } from "./provider-jsonrpc.js";
const defaultApplicationId = "62e1ad51b37b8e00394bda3b";
function getHost(name) {
    switch (name) {
        case "mainnet":
            return "eth-mainnet.gateway.pokt.network";
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
export class PocketProvider extends JsonRpcProvider {
    /**
     *  The Application ID for the Pocket connection.
     */
    applicationId;
    /**
     *  The Application Secret for making authenticated requests
     *  to the Pocket connection.
     */
    applicationSecret;
    /**
     *  Create a new **PocketProvider**.
     *
     *  By default connecting to ``mainnet`` with a highly throttled
     *  API key.
     */
    constructor(_network, applicationId, applicationSecret) {
        if (_network == null) {
            _network = "mainnet";
        }
        const network = Network.from(_network);
        if (applicationId == null) {
            applicationId = defaultApplicationId;
        }
        if (applicationSecret == null) {
            applicationSecret = null;
        }
        const options = { staticNetwork: network };
        const request = PocketProvider.getRequest(network, applicationId, applicationSecret);
        super(request, network, options);
        defineProperties(this, { applicationId, applicationSecret });
    }
    _getProvider(chainId) {
        try {
            return new PocketProvider(chainId, this.applicationId, this.applicationSecret);
        }
        catch (error) { }
        return super._getProvider(chainId);
    }
    /**
     *  Returns a prepared request for connecting to %%network%% with
     *  %%applicationId%%.
     */
    static getRequest(network, applicationId, applicationSecret) {
        if (applicationId == null) {
            applicationId = defaultApplicationId;
        }
        const request = new FetchRequest(`https:/\/${getHost(network.name)}/v1/lb/${applicationId}`);
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
    isCommunityResource() {
        return (this.applicationId === defaultApplicationId);
    }
}
//# sourceMappingURL=provider-pocket.js.map