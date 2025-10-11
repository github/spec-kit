"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AnkrProvider = void 0;
/**
 *  [[link-ankr]] provides a third-party service for connecting to
 *  various blockchains over JSON-RPC.
 *
 *  **Supported Networks**
 *
 *  - Ethereum Mainnet (``mainnet``)
 *  - Goerli Testnet (``goerli``)
 *  - Sepolia Testnet (``sepolia``)
 *  - Arbitrum (``arbitrum``)
 *  - Base (``base``)
 *  - Base Goerlia Testnet (``base-goerli``)
 *  - Base Sepolia Testnet (``base-sepolia``)
 *  - BNB (``bnb``)
 *  - BNB Testnet (``bnbt``)
 *  - Optimism (``optimism``)
 *  - Optimism Goerli Testnet (``optimism-goerli``)
 *  - Optimism Sepolia Testnet (``optimism-sepolia``)
 *  - Polygon (``matic``)
 *  - Polygon Mumbai Testnet (``matic-mumbai``)
 *
 *  @_subsection: api/providers/thirdparty:Ankr  [providers-ankr]
 */
const index_js_1 = require("../utils/index.js");
const community_js_1 = require("./community.js");
const network_js_1 = require("./network.js");
const provider_jsonrpc_js_1 = require("./provider-jsonrpc.js");
const defaultApiKey = "9f7d929b018cdffb338517efa06f58359e86ff1ffd350bc889738523659e7972";
function getHost(name) {
    switch (name) {
        case "mainnet":
            return "rpc.ankr.com/eth";
        case "goerli":
            return "rpc.ankr.com/eth_goerli";
        case "sepolia":
            return "rpc.ankr.com/eth_sepolia";
        case "arbitrum":
            return "rpc.ankr.com/arbitrum";
        case "base":
            return "rpc.ankr.com/base";
        case "base-goerli":
            return "rpc.ankr.com/base_goerli";
        case "base-sepolia":
            return "rpc.ankr.com/base_sepolia";
        case "bnb":
            return "rpc.ankr.com/bsc";
        case "bnbt":
            return "rpc.ankr.com/bsc_testnet_chapel";
        case "matic":
            return "rpc.ankr.com/polygon";
        case "matic-mumbai":
            return "rpc.ankr.com/polygon_mumbai";
        case "optimism":
            return "rpc.ankr.com/optimism";
        case "optimism-goerli":
            return "rpc.ankr.com/optimism_testnet";
        case "optimism-sepolia":
            return "rpc.ankr.com/optimism_sepolia";
    }
    (0, index_js_1.assertArgument)(false, "unsupported network", "network", name);
}
/**
 *  The **AnkrProvider** connects to the [[link-ankr]]
 *  JSON-RPC end-points.
 *
 *  By default, a highly-throttled API key is used, which is
 *  appropriate for quick prototypes and simple scripts. To
 *  gain access to an increased rate-limit, it is highly
 *  recommended to [sign up here](link-ankr-signup).
 */
class AnkrProvider extends provider_jsonrpc_js_1.JsonRpcProvider {
    /**
     *  The API key for the Ankr connection.
     */
    apiKey;
    /**
     *  Create a new **AnkrProvider**.
     *
     *  By default connecting to ``mainnet`` with a highly throttled
     *  API key.
     */
    constructor(_network, apiKey) {
        if (_network == null) {
            _network = "mainnet";
        }
        const network = network_js_1.Network.from(_network);
        if (apiKey == null) {
            apiKey = defaultApiKey;
        }
        // Ankr does not support filterId, so we force polling
        const options = { polling: true, staticNetwork: network };
        const request = AnkrProvider.getRequest(network, apiKey);
        super(request, network, options);
        (0, index_js_1.defineProperties)(this, { apiKey });
    }
    _getProvider(chainId) {
        try {
            return new AnkrProvider(chainId, this.apiKey);
        }
        catch (error) { }
        return super._getProvider(chainId);
    }
    /**
     *  Returns a prepared request for connecting to %%network%% with
     *  %%apiKey%%.
     */
    static getRequest(network, apiKey) {
        if (apiKey == null) {
            apiKey = defaultApiKey;
        }
        const request = new index_js_1.FetchRequest(`https:/\/${getHost(network.name)}/${apiKey}`);
        request.allowGzip = true;
        if (apiKey === defaultApiKey) {
            request.retryFunc = async (request, response, attempt) => {
                (0, community_js_1.showThrottleMessage)("AnkrProvider");
                return true;
            };
        }
        return request;
    }
    getRpcError(payload, error) {
        if (payload.method === "eth_sendRawTransaction") {
            if (error && error.error && error.error.message === "INTERNAL_ERROR: could not replace existing tx") {
                error.error.message = "replacement transaction underpriced";
            }
        }
        return super.getRpcError(payload, error);
    }
    isCommunityResource() {
        return (this.apiKey === defaultApiKey);
    }
}
exports.AnkrProvider = AnkrProvider;
//# sourceMappingURL=provider-ankr.js.map