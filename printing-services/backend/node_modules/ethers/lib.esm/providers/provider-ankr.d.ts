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
import { FetchRequest } from "../utils/index.js";
import { AbstractProvider } from "./abstract-provider.js";
import { Network } from "./network.js";
import { JsonRpcProvider } from "./provider-jsonrpc.js";
import type { CommunityResourcable } from "./community.js";
import type { Networkish } from "./network.js";
import type { JsonRpcError, JsonRpcPayload } from "./provider-jsonrpc.js";
/**
 *  The **AnkrProvider** connects to the [[link-ankr]]
 *  JSON-RPC end-points.
 *
 *  By default, a highly-throttled API key is used, which is
 *  appropriate for quick prototypes and simple scripts. To
 *  gain access to an increased rate-limit, it is highly
 *  recommended to [sign up here](link-ankr-signup).
 */
export declare class AnkrProvider extends JsonRpcProvider implements CommunityResourcable {
    /**
     *  The API key for the Ankr connection.
     */
    readonly apiKey: string;
    /**
     *  Create a new **AnkrProvider**.
     *
     *  By default connecting to ``mainnet`` with a highly throttled
     *  API key.
     */
    constructor(_network?: Networkish, apiKey?: null | string);
    _getProvider(chainId: number): AbstractProvider;
    /**
     *  Returns a prepared request for connecting to %%network%% with
     *  %%apiKey%%.
     */
    static getRequest(network: Network, apiKey?: null | string): FetchRequest;
    getRpcError(payload: JsonRpcPayload, error: JsonRpcError): Error;
    isCommunityResource(): boolean;
}
//# sourceMappingURL=provider-ankr.d.ts.map