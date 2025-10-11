"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PocketProvider = void 0;
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
const index_js_1 = require("../utils/index.js");
const community_js_1 = require("./community.js");
const network_js_1 = require("./network.js");
const provider_jsonrpc_js_1 = require("./provider-jsonrpc.js");
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
    (0, index_js_1.assertArgument)(false, "unsupported network", "network", name);
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
class PocketProvider extends provider_jsonrpc_js_1.JsonRpcProvider {
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
        const network = network_js_1.Network.from(_network);
        if (applicationId == null) {
            applicationId = defaultApplicationId;
        }
        if (applicationSecret == null) {
            applicationSecret = null;
        }
        const options = { staticNetwork: network };
        const request = PocketProvider.getRequest(network, applicationId, applicationSecret);
        super(request, network, options);
        (0, index_js_1.defineProperties)(this, { applicationId, applicationSecret });
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
        const request = new index_js_1.FetchRequest(`https:/\/${getHost(network.name)}/v1/lb/${applicationId}`);
        request.allowGzip = true;
        if (applicationSecret) {
            request.setCredentials("", applicationSecret);
        }
        if (applicationId === defaultApplicationId) {
            request.retryFunc = async (request, response, attempt) => {
                (0, community_js_1.showThrottleMessage)("PocketProvider");
                return true;
            };
        }
        return request;
    }
    isCommunityResource() {
        return (this.applicationId === defaultApplicationId);
    }
}
exports.PocketProvider = PocketProvider;
//# sourceMappingURL=provider-pocket.js.map