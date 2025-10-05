"use strict";
/**
 *  [[link-alchemy]] provides a third-party service for connecting to
 *  various blockchains over JSON-RPC.
 *
 *  **Supported Networks**
 *
 *  - Ethereum Mainnet (``mainnet``)
 *  - Goerli Testnet (``goerli``)
 *  - Sepolia Testnet (``sepolia``)
 *  - Arbitrum (``arbitrum``)
 *  - Arbitrum Goerli Testnet (``arbitrum-goerli``)
 *  - Arbitrum Sepolia Testnet (``arbitrum-sepolia``)
 *  - Base (``base``)
 *  - Base Goerlia Testnet (``base-goerli``)
 *  - Base Sepolia Testnet (``base-sepolia``)
 *  - Optimism (``optimism``)
 *  - Optimism Goerli Testnet (``optimism-goerli``)
 *  - Optimism Sepolia Testnet (``optimism-sepolia``)
 *  - Polygon (``matic``)
 *  - Polygon Amoy Testnet (``matic-amoy``)
 *  - Polygon Mumbai Testnet (``matic-mumbai``)
 *
 *  @_subsection: api/providers/thirdparty:Alchemy  [providers-alchemy]
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.AlchemyProvider = void 0;
const index_js_1 = require("../utils/index.js");
const community_js_1 = require("./community.js");
const network_js_1 = require("./network.js");
const provider_jsonrpc_js_1 = require("./provider-jsonrpc.js");
const defaultApiKey = "_gg7wSSi0KMBsdKnGVfHDueq6xMB9EkC";
function getHost(name) {
    switch (name) {
        case "mainnet":
            return "eth-mainnet.alchemyapi.io";
        case "goerli":
            return "eth-goerli.g.alchemy.com";
        case "sepolia":
            return "eth-sepolia.g.alchemy.com";
        case "arbitrum":
            return "arb-mainnet.g.alchemy.com";
        case "arbitrum-goerli":
            return "arb-goerli.g.alchemy.com";
        case "arbitrum-sepolia":
            return "arb-sepolia.g.alchemy.com";
        case "base":
            return "base-mainnet.g.alchemy.com";
        case "base-goerli":
            return "base-goerli.g.alchemy.com";
        case "base-sepolia":
            return "base-sepolia.g.alchemy.com";
        case "matic":
            return "polygon-mainnet.g.alchemy.com";
        case "matic-amoy":
            return "polygon-amoy.g.alchemy.com";
        case "matic-mumbai":
            return "polygon-mumbai.g.alchemy.com";
        case "optimism":
            return "opt-mainnet.g.alchemy.com";
        case "optimism-goerli":
            return "opt-goerli.g.alchemy.com";
        case "optimism-sepolia":
            return "opt-sepolia.g.alchemy.com";
    }
    (0, index_js_1.assertArgument)(false, "unsupported network", "network", name);
}
/**
 *  The **AlchemyProvider** connects to the [[link-alchemy]]
 *  JSON-RPC end-points.
 *
 *  By default, a highly-throttled API key is used, which is
 *  appropriate for quick prototypes and simple scripts. To
 *  gain access to an increased rate-limit, it is highly
 *  recommended to [sign up here](link-alchemy-signup).
 *
 *  @_docloc: api/providers/thirdparty
 */
class AlchemyProvider extends provider_jsonrpc_js_1.JsonRpcProvider {
    apiKey;
    constructor(_network, apiKey) {
        if (_network == null) {
            _network = "mainnet";
        }
        const network = network_js_1.Network.from(_network);
        if (apiKey == null) {
            apiKey = defaultApiKey;
        }
        const request = AlchemyProvider.getRequest(network, apiKey);
        super(request, network, { staticNetwork: network });
        (0, index_js_1.defineProperties)(this, { apiKey });
    }
    _getProvider(chainId) {
        try {
            return new AlchemyProvider(chainId, this.apiKey);
        }
        catch (error) { }
        return super._getProvider(chainId);
    }
    async _perform(req) {
        // https://docs.alchemy.com/reference/trace-transaction
        if (req.method === "getTransactionResult") {
            const { trace, tx } = await (0, index_js_1.resolveProperties)({
                trace: this.send("trace_transaction", [req.hash]),
                tx: this.getTransaction(req.hash)
            });
            if (trace == null || tx == null) {
                return null;
            }
            let data;
            let error = false;
            try {
                data = trace[0].result.output;
                error = (trace[0].error === "Reverted");
            }
            catch (error) { }
            if (data) {
                (0, index_js_1.assert)(!error, "an error occurred during transaction executions", "CALL_EXCEPTION", {
                    action: "getTransactionResult",
                    data,
                    reason: null,
                    transaction: tx,
                    invocation: null,
                    revert: null // @TODO
                });
                return data;
            }
            (0, index_js_1.assert)(false, "could not parse trace result", "BAD_DATA", { value: trace });
        }
        return await super._perform(req);
    }
    isCommunityResource() {
        return (this.apiKey === defaultApiKey);
    }
    static getRequest(network, apiKey) {
        if (apiKey == null) {
            apiKey = defaultApiKey;
        }
        const request = new index_js_1.FetchRequest(`https:/\/${getHost(network.name)}/v2/${apiKey}`);
        request.allowGzip = true;
        if (apiKey === defaultApiKey) {
            request.retryFunc = async (request, response, attempt) => {
                (0, community_js_1.showThrottleMessage)("alchemy");
                return true;
            };
        }
        return request;
    }
}
exports.AlchemyProvider = AlchemyProvider;
//# sourceMappingURL=provider-alchemy.js.map