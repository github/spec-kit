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
import { FetchRequest } from "../utils/index.js";
import { Network } from "./network.js";
import { JsonRpcProvider } from "./provider-jsonrpc.js";
import { WebSocketProvider } from "./provider-websocket.js";
import type { AbstractProvider } from "./abstract-provider.js";
import type { CommunityResourcable } from "./community.js";
import type { Networkish } from "./network.js";
/**
 *  The **InfuraWebSocketProvider** connects to the [[link-infura]]
 *  WebSocket end-points.
 *
 *  By default, a highly-throttled API key is used, which is
 *  appropriate for quick prototypes and simple scripts. To
 *  gain access to an increased rate-limit, it is highly
 *  recommended to [sign up here](link-infura-signup).
 */
export declare class InfuraWebSocketProvider extends WebSocketProvider implements CommunityResourcable {
    /**
     *  The Project ID for the INFURA connection.
     */
    readonly projectId: string;
    /**
     *  The Project Secret.
     *
     *  If null, no authenticated requests are made. This should not
     *  be used outside of private contexts.
     */
    readonly projectSecret: null | string;
    /**
     *  Creates a new **InfuraWebSocketProvider**.
     */
    constructor(network?: Networkish, projectId?: string);
    isCommunityResource(): boolean;
}
/**
 *  The **InfuraProvider** connects to the [[link-infura]]
 *  JSON-RPC end-points.
 *
 *  By default, a highly-throttled API key is used, which is
 *  appropriate for quick prototypes and simple scripts. To
 *  gain access to an increased rate-limit, it is highly
 *  recommended to [sign up here](link-infura-signup).
 */
export declare class InfuraProvider extends JsonRpcProvider implements CommunityResourcable {
    /**
     *  The Project ID for the INFURA connection.
     */
    readonly projectId: string;
    /**
     *  The Project Secret.
     *
     *  If null, no authenticated requests are made. This should not
     *  be used outside of private contexts.
     */
    readonly projectSecret: null | string;
    /**
     *  Creates a new **InfuraProvider**.
     */
    constructor(_network?: Networkish, projectId?: null | string, projectSecret?: null | string);
    _getProvider(chainId: number): AbstractProvider;
    isCommunityResource(): boolean;
    /**
     *  Creates a new **InfuraWebSocketProvider**.
     */
    static getWebSocketProvider(network?: Networkish, projectId?: string): InfuraWebSocketProvider;
    /**
     *  Returns a prepared request for connecting to %%network%%
     *  with %%projectId%% and %%projectSecret%%.
     */
    static getRequest(network: Network, projectId?: null | string, projectSecret?: null | string): FetchRequest;
}
//# sourceMappingURL=provider-infura.d.ts.map