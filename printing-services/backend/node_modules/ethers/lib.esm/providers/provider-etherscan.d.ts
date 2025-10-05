/**
 *  [[link-etherscan]] provides a third-party service for connecting to
 *  various blockchains over a combination of JSON-RPC and custom API
 *  endpoints.
 *
 *  **Supported Networks**
 *
 *  - Ethereum Mainnet (``mainnet``)
 *  - Goerli Testnet (``goerli``)
 *  - Sepolia Testnet (``sepolia``)
 *  - Holesky Testnet (``holesky``)
 *  - Arbitrum (``arbitrum``)
 *  - Arbitrum Goerli Testnet (``arbitrum-goerli``)
 *  - Base (``base``)
 *  - Base Sepolia Testnet (``base-sepolia``)
 *  - BNB Smart Chain Mainnet (``bnb``)
 *  - BNB Smart Chain Testnet (``bnbt``)
 *  - Optimism (``optimism``)
 *  - Optimism Goerli Testnet (``optimism-goerli``)
 *  - Polygon (``matic``)
 *  - Polygon Mumbai Testnet (``matic-mumbai``)
 *  - Polygon Amoy Testnet (``matic-amoy``)
 *
 *  @_subsection api/providers/thirdparty:Etherscan  [providers-etherscan]
 */
import { Contract } from "../contract/index.js";
import { AbstractProvider } from "./abstract-provider.js";
import { Network } from "./network.js";
import { NetworkPlugin } from "./plugins-network.js";
import { PerformActionRequest } from "./abstract-provider.js";
import type { Networkish } from "./network.js";
import type { TransactionRequest } from "./provider.js";
/**
 *  When subscribing to the ``"debug"`` event on an Etherscan-based
 *  provider, the events receive a **DebugEventEtherscanProvider**
 *  payload.
 *
 *  @_docloc: api/providers/thirdparty:Etherscan
 */
export type DebugEventEtherscanProvider = {
    action: "sendRequest";
    id: number;
    url: string;
    payload: Record<string, any>;
} | {
    action: "receiveRequest";
    id: number;
    result: any;
} | {
    action: "receiveError";
    id: number;
    error: any;
};
/**
 *  A Network can include an **EtherscanPlugin** to provide
 *  a custom base URL.
 *
 *  @_docloc: api/providers/thirdparty:Etherscan
 */
export declare class EtherscanPlugin extends NetworkPlugin {
    /**
     *  The Etherscan API base URL.
     */
    readonly baseUrl: string;
    /**
     *  Creates a new **EtherscanProvider** which will use
     *  %%baseUrl%%.
     */
    constructor(baseUrl: string);
    clone(): EtherscanPlugin;
}
/**
 *  The **EtherscanBaseProvider** is the super-class of
 *  [[EtherscanProvider]], which should generally be used instead.
 *
 *  Since the **EtherscanProvider** includes additional code for
 *  [[Contract]] access, in //rare cases// that contracts are not
 *  used, this class can reduce code size.
 *
 *  @_docloc: api/providers/thirdparty:Etherscan
 */
export declare class EtherscanProvider extends AbstractProvider {
    #private;
    /**
     *  The connected network.
     */
    readonly network: Network;
    /**
     *  The API key or null if using the community provided bandwidth.
     */
    readonly apiKey: null | string;
    /**
     *  Creates a new **EtherscanBaseProvider**.
     */
    constructor(_network?: Networkish, _apiKey?: string);
    /**
     *  Returns the base URL.
     *
     *  If an [[EtherscanPlugin]] is configured on the
     *  [[EtherscanBaseProvider_network]], returns the plugin's
     *  baseUrl.
     *
     *  Deprecated; for Etherscan v2 the base is no longer a simply
     *  host, but instead a URL including a chainId parameter. Changing
     *  this to return a URL prefix could break some libraries, so it
     *  is left intact but will be removed in the future as it is unused.
     */
    getBaseUrl(): string;
    /**
     *  Returns the URL for the %%module%% and %%params%%.
     */
    getUrl(module: string, params: Record<string, string>): string;
    /**
     *  Returns the URL for using POST requests.
     */
    getPostUrl(): string;
    /**
     *  Returns the parameters for using POST requests.
     */
    getPostData(module: string, params: Record<string, any>): Record<string, any>;
    detectNetwork(): Promise<Network>;
    /**
     *  Resolves to the result of calling %%module%% with %%params%%.
     *
     *  If %%post%%, the request is made as a POST request.
     */
    fetch(module: string, params: Record<string, any>, post?: boolean): Promise<any>;
    /**
     *  Returns %%transaction%% normalized for the Etherscan API.
     */
    _getTransactionPostData(transaction: TransactionRequest): Record<string, string>;
    /**
     *  Throws the normalized Etherscan error.
     */
    _checkError(req: PerformActionRequest, error: Error, transaction: any): never;
    _detectNetwork(): Promise<Network>;
    _perform(req: PerformActionRequest): Promise<any>;
    getNetwork(): Promise<Network>;
    /**
     *  Resolves to the current price of ether.
     *
     *  This returns ``0`` on any network other than ``mainnet``.
     */
    getEtherPrice(): Promise<number>;
    /**
     *  Resolves to a [Contract]] for %%address%%, using the
     *  Etherscan API to retreive the Contract ABI.
     */
    getContract(_address: string): Promise<null | Contract>;
    isCommunityResource(): boolean;
}
//# sourceMappingURL=provider-etherscan.d.ts.map