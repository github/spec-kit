"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.InfuraProvider = exports.InfuraWebSocketProvider = void 0;
/**
 *  [[link-infura]] provides a third-party service for connecting to
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
 *  - BNB Smart Chain Mainnet (``bnb``)
 *  - BNB Smart Chain Testnet (``bnbt``)
 *  - Linea (``linea``)
 *  - Linea Goerli Testnet (``linea-goerli``)
 *  - Linea Sepolia Testnet (``linea-sepolia``)
 *  - Optimism (``optimism``)
 *  - Optimism Goerli Testnet (``optimism-goerli``)
 *  - Optimism Sepolia Testnet (``optimism-sepolia``)
 *  - Polygon (``matic``)
 *  - Polygon Amoy Testnet (``matic-amoy``)
 *  - Polygon Mumbai Testnet (``matic-mumbai``)
 *
 *  @_subsection: api/providers/thirdparty:INFURA  [providers-infura]
 */
const index_js_1 = require("../utils/index.js");
const community_js_1 = require("./community.js");
const network_js_1 = require("./network.js");
const provider_jsonrpc_js_1 = require("./provider-jsonrpc.js");
const provider_websocket_js_1 = require("./provider-websocket.js");
const defaultProjectId = "84842078b09946638c03157f83405213";
function getHost(name) {
    switch (name) {
        case "mainnet":
            return "mainnet.infura.io";
        case "goerli":
            return "goerli.infura.io";
        case "sepolia":
            return "sepolia.infura.io";
        case "arbitrum":
            return "arbitrum-mainnet.infura.io";
        case "arbitrum-goerli":
            return "arbitrum-goerli.infura.io";
        case "arbitrum-sepolia":
            return "arbitrum-sepolia.infura.io";
        case "base":
            return "base-mainnet.infura.io";
        case "base-goerlia": // @TODO: Remove this typo in the future!
        case "base-goerli":
            return "base-goerli.infura.io";
        case "base-sepolia":
            return "base-sepolia.infura.io";
        case "bnb":
            return "bsc-mainnet.infura.io";
        case "bnbt":
            return "bsc-testnet.infura.io";
        case "linea":
            return "linea-mainnet.infura.io";
        case "linea-goerli":
            return "linea-goerli.infura.io";
        case "linea-sepolia":
            return "linea-sepolia.infura.io";
        case "matic":
            return "polygon-mainnet.infura.io";
        case "matic-amoy":
            return "polygon-amoy.infura.io";
        case "matic-mumbai":
            return "polygon-mumbai.infura.io";
        case "optimism":
            return "optimism-mainnet.infura.io";
        case "optimism-goerli":
            return "optimism-goerli.infura.io";
        case "optimism-sepolia":
            return "optimism-sepolia.infura.io";
    }
    (0, index_js_1.assertArgument)(false, "unsupported network", "network", name);
}
/**
 *  The **InfuraWebSocketProvider** connects to the [[link-infura]]
 *  WebSocket end-points.
 *
 *  By default, a highly-throttled API key is used, which is
 *  appropriate for quick prototypes and simple scripts. To
 *  gain access to an increased rate-limit, it is highly
 *  recommended to [sign up here](link-infura-signup).
 */
class InfuraWebSocketProvider extends provider_websocket_js_1.WebSocketProvider {
    /**
     *  The Project ID for the INFURA connection.
     */
    projectId;
    /**
     *  The Project Secret.
     *
     *  If null, no authenticated requests are made. This should not
     *  be used outside of private contexts.
     */
    projectSecret;
    /**
     *  Creates a new **InfuraWebSocketProvider**.
     */
    constructor(network, projectId) {
        const provider = new InfuraProvider(network, projectId);
        const req = provider._getConnection();
        (0, index_js_1.assert)(!req.credentials, "INFURA WebSocket project secrets unsupported", "UNSUPPORTED_OPERATION", { operation: "InfuraProvider.getWebSocketProvider()" });
        const url = req.url.replace(/^http/i, "ws").replace("/v3/", "/ws/v3/");
        super(url, provider._network);
        (0, index_js_1.defineProperties)(this, {
            projectId: provider.projectId,
            projectSecret: provider.projectSecret
        });
    }
    isCommunityResource() {
        return (this.projectId === defaultProjectId);
    }
}
exports.InfuraWebSocketProvider = InfuraWebSocketProvider;
/**
 *  The **InfuraProvider** connects to the [[link-infura]]
 *  JSON-RPC end-points.
 *
 *  By default, a highly-throttled API key is used, which is
 *  appropriate for quick prototypes and simple scripts. To
 *  gain access to an increased rate-limit, it is highly
 *  recommended to [sign up here](link-infura-signup).
 */
class InfuraProvider extends provider_jsonrpc_js_1.JsonRpcProvider {
    /**
     *  The Project ID for the INFURA connection.
     */
    projectId;
    /**
     *  The Project Secret.
     *
     *  If null, no authenticated requests are made. This should not
     *  be used outside of private contexts.
     */
    projectSecret;
    /**
     *  Creates a new **InfuraProvider**.
     */
    constructor(_network, projectId, projectSecret) {
        if (_network == null) {
            _network = "mainnet";
        }
        const network = network_js_1.Network.from(_network);
        if (projectId == null) {
            projectId = defaultProjectId;
        }
        if (projectSecret == null) {
            projectSecret = null;
        }
        const request = InfuraProvider.getRequest(network, projectId, projectSecret);
        super(request, network, { staticNetwork: network });
        (0, index_js_1.defineProperties)(this, { projectId, projectSecret });
    }
    _getProvider(chainId) {
        try {
            return new InfuraProvider(chainId, this.projectId, this.projectSecret);
        }
        catch (error) { }
        return super._getProvider(chainId);
    }
    isCommunityResource() {
        return (this.projectId === defaultProjectId);
    }
    /**
     *  Creates a new **InfuraWebSocketProvider**.
     */
    static getWebSocketProvider(network, projectId) {
        return new InfuraWebSocketProvider(network, projectId);
    }
    /**
     *  Returns a prepared request for connecting to %%network%%
     *  with %%projectId%% and %%projectSecret%%.
     */
    static getRequest(network, projectId, projectSecret) {
        if (projectId == null) {
            projectId = defaultProjectId;
        }
        if (projectSecret == null) {
            projectSecret = null;
        }
        const request = new index_js_1.FetchRequest(`https:/\/${getHost(network.name)}/v3/${projectId}`);
        request.allowGzip = true;
        if (projectSecret) {
            request.setCredentials("", projectSecret);
        }
        if (projectId === defaultProjectId) {
            request.retryFunc = async (request, response, attempt) => {
                (0, community_js_1.showThrottleMessage)("InfuraProvider");
                return true;
            };
        }
        return request;
    }
}
exports.InfuraProvider = InfuraProvider;
//# sourceMappingURL=provider-infura.js.map