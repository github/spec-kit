"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChainstackProvider = void 0;
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
const index_js_1 = require("../utils/index.js");
const community_js_1 = require("./community.js");
const network_js_1 = require("./network.js");
const provider_jsonrpc_js_1 = require("./provider-jsonrpc.js");
function getApiKey(name) {
    switch (name) {
        case "mainnet": return "39f1d67cedf8b7831010a665328c9197";
        case "arbitrum": return "0550c209db33c3abf4cc927e1e18cea1";
        case "bnb": return "98b5a77e531614387366f6fc5da097f8";
        case "matic": return "cd9d4d70377471aa7c142ec4a4205249";
    }
    (0, index_js_1.assertArgument)(false, "unsupported network", "network", name);
}
function getHost(name) {
    switch (name) {
        case "mainnet":
            return "ethereum-mainnet.core.chainstack.com";
        case "arbitrum":
            return "arbitrum-mainnet.core.chainstack.com";
        case "bnb":
            return "bsc-mainnet.core.chainstack.com";
        case "matic":
            return "polygon-mainnet.core.chainstack.com";
    }
    (0, index_js_1.assertArgument)(false, "unsupported network", "network", name);
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
class ChainstackProvider extends provider_jsonrpc_js_1.JsonRpcProvider {
    /**
     *  The API key for the Chainstack connection.
     */
    apiKey;
    /**
     *  Creates a new **ChainstackProvider**.
     */
    constructor(_network, apiKey) {
        if (_network == null) {
            _network = "mainnet";
        }
        const network = network_js_1.Network.from(_network);
        if (apiKey == null) {
            apiKey = getApiKey(network.name);
        }
        const request = ChainstackProvider.getRequest(network, apiKey);
        super(request, network, { staticNetwork: network });
        (0, index_js_1.defineProperties)(this, { apiKey });
    }
    _getProvider(chainId) {
        try {
            return new ChainstackProvider(chainId, this.apiKey);
        }
        catch (error) { }
        return super._getProvider(chainId);
    }
    isCommunityResource() {
        return (this.apiKey === getApiKey(this._network.name));
    }
    /**
     *  Returns a prepared request for connecting to %%network%%
     *  with %%apiKey%% and %%projectSecret%%.
     */
    static getRequest(network, apiKey) {
        if (apiKey == null) {
            apiKey = getApiKey(network.name);
        }
        const request = new index_js_1.FetchRequest(`https:/\/${getHost(network.name)}/${apiKey}`);
        request.allowGzip = true;
        if (apiKey === getApiKey(network.name)) {
            request.retryFunc = async (request, response, attempt) => {
                (0, community_js_1.showThrottleMessage)("ChainstackProvider");
                return true;
            };
        }
        return request;
    }
}
exports.ChainstackProvider = ChainstackProvider;
//# sourceMappingURL=provider-chainstack.js.map