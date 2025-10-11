/**
 *  [[link-blockscout]] provides a third-party service for connecting to
 *  various blockchains over JSON-RPC.
 *
 *  **Supported Networks**
 *
 *  - Ethereum Mainnet (``mainnet``)
 *  - Sepolia Testnet (``sepolia``)
 *  - Holesky Testnet (``holesky``)
 *  - Ethereum Classic (``classic``)
 *  - Arbitrum (``arbitrum``)
 *  - Base (``base``)
 *  - Base Sepolia Testnet (``base-sepolia``)
 *  - Gnosis (``xdai``)
 *  - Optimism (``optimism``)
 *  - Optimism Sepolia Testnet (``optimism-sepolia``)
 *  - Polygon (``matic``)
 *
 *  @_subsection: api/providers/thirdparty:Blockscout  [providers-blockscout]
 */
import { FetchRequest } from "../utils/index.js";
import { Network } from "./network.js";
import { JsonRpcProvider } from "./provider-jsonrpc.js";
import type { AbstractProvider, PerformActionRequest } from "./abstract-provider.js";
import type { CommunityResourcable } from "./community.js";
import type { Networkish } from "./network.js";
import type { JsonRpcPayload, JsonRpcError } from "./provider-jsonrpc.js";
/**
 *  The **BlockscoutProvider** connects to the [[link-blockscout]]
 *  JSON-RPC end-points.
 *
 *  By default, a highly-throttled API key is used, which is
 *  appropriate for quick prototypes and simple scripts. To
 *  gain access to an increased rate-limit, it is highly
 *  recommended to [sign up here](link-blockscout).
 */
export declare class BlockscoutProvider extends JsonRpcProvider implements CommunityResourcable {
    /**
     *  The API key.
     */
    readonly apiKey: null | string;
    /**
     *  Creates a new **BlockscoutProvider**.
     */
    constructor(_network?: Networkish, apiKey?: null | string);
    _getProvider(chainId: number): AbstractProvider;
    isCommunityResource(): boolean;
    getRpcRequest(req: PerformActionRequest): null | {
        method: string;
        args: Array<any>;
    };
    getRpcError(payload: JsonRpcPayload, _error: JsonRpcError): Error;
    /**
     *  Returns a prepared request for connecting to %%network%%
     *  with %%apiKey%%.
     */
    static getRequest(network: Network): FetchRequest;
}
//# sourceMappingURL=provider-blockscout.d.ts.map