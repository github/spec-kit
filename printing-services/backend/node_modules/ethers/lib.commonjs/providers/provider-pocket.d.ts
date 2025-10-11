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
import { FetchRequest } from "../utils/index.js";
import { AbstractProvider } from "./abstract-provider.js";
import { Network } from "./network.js";
import { JsonRpcProvider } from "./provider-jsonrpc.js";
import type { CommunityResourcable } from "./community.js";
import type { Networkish } from "./network.js";
/**
 *  The **PocketProvider** connects to the [[link-pocket]]
 *  JSON-RPC end-points.
 *
 *  By default, a highly-throttled API key is used, which is
 *  appropriate for quick prototypes and simple scripts. To
 *  gain access to an increased rate-limit, it is highly
 *  recommended to [sign up here](link-pocket-signup).
 */
export declare class PocketProvider extends JsonRpcProvider implements CommunityResourcable {
    /**
     *  The Application ID for the Pocket connection.
     */
    readonly applicationId: string;
    /**
     *  The Application Secret for making authenticated requests
     *  to the Pocket connection.
     */
    readonly applicationSecret: null | string;
    /**
     *  Create a new **PocketProvider**.
     *
     *  By default connecting to ``mainnet`` with a highly throttled
     *  API key.
     */
    constructor(_network?: Networkish, applicationId?: null | string, applicationSecret?: null | string);
    _getProvider(chainId: number): AbstractProvider;
    /**
     *  Returns a prepared request for connecting to %%network%% with
     *  %%applicationId%%.
     */
    static getRequest(network: Network, applicationId?: null | string, applicationSecret?: null | string): FetchRequest;
    isCommunityResource(): boolean;
}
//# sourceMappingURL=provider-pocket.d.ts.map