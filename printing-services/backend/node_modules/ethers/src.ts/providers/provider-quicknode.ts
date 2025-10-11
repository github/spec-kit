/**
 *  [[link-quicknode]] provides a third-party service for connecting to
 *  various blockchains over JSON-RPC.
 *
 *  **Supported Networks**
 *
 *  - Ethereum Mainnet (``mainnet``)
 *  - Goerli Testnet (``goerli``)
 *  - Sepolia Testnet (``sepolia``)
 *  - Holesky Testnet (``holesky``)
 *  - Arbitrum (``arbitrum``)
 *  - Arbitrum Goerli Testnet (``arbitrum-goerli``)
 *  - Arbitrum Sepolia Testnet (``arbitrum-sepolia``)
 *  - Base Mainnet (``base``);
 *  - Base Goerli Testnet (``base-goerli``);
 *  - Base Sepolia Testnet (``base-sepolia``);
 *  - BNB Smart Chain Mainnet (``bnb``)
 *  - BNB Smart Chain Testnet (``bnbt``)
 *  - Optimism (``optimism``)
 *  - Optimism Goerli Testnet (``optimism-goerli``)
 *  - Optimism Sepolia Testnet (``optimism-sepolia``)
 *  - Polygon (``matic``)
 *  - Polygon Mumbai Testnet (``matic-mumbai``)
 *
 *  @_subsection: api/providers/thirdparty:QuickNode  [providers-quicknode]
 */

import {
    defineProperties, FetchRequest, assertArgument
} from "../utils/index.js";

import { showThrottleMessage } from "./community.js";
import { Network } from "./network.js";
import { JsonRpcProvider } from "./provider-jsonrpc.js";

import type { AbstractProvider } from "./abstract-provider.js";
import type { CommunityResourcable } from "./community.js";
import type { Networkish } from "./network.js";


const defaultToken = "919b412a057b5e9c9b6dce193c5a60242d6efadb";

function getHost(name: string): string {
    switch(name) {
        case "mainnet":
            return "ethers.quiknode.pro";
        case "goerli":
            return "ethers.ethereum-goerli.quiknode.pro";
        case "sepolia":
            return "ethers.ethereum-sepolia.quiknode.pro";
        case "holesky":
            return "ethers.ethereum-holesky.quiknode.pro";

        case "arbitrum":
            return "ethers.arbitrum-mainnet.quiknode.pro";
        case "arbitrum-goerli":
            return "ethers.arbitrum-goerli.quiknode.pro";
        case "arbitrum-sepolia":
            return "ethers.arbitrum-sepolia.quiknode.pro";
        case "base":
            return "ethers.base-mainnet.quiknode.pro";
        case "base-goerli":
            return "ethers.base-goerli.quiknode.pro";
        case "base-spolia":
            return "ethers.base-sepolia.quiknode.pro";
        case "bnb":
            return "ethers.bsc.quiknode.pro";
        case "bnbt":
            return "ethers.bsc-testnet.quiknode.pro";
        case "matic":
            return "ethers.matic.quiknode.pro";
        case "matic-mumbai":
            return "ethers.matic-testnet.quiknode.pro";
        case "optimism":
            return "ethers.optimism.quiknode.pro";
        case "optimism-goerli":
            return "ethers.optimism-goerli.quiknode.pro";
        case "optimism-sepolia":
            return "ethers.optimism-sepolia.quiknode.pro";
        case "xdai":
            return "ethers.xdai.quiknode.pro";
    }

    assertArgument(false, "unsupported network", "network", name);
}

/*
@TODO:
  These networks are not currently present in the Network
  default included networks. Research them and ensure they
  are EVM compatible and work with ethers

  http://ethers.matic-amoy.quiknode.pro

  http://ethers.avalanche-mainnet.quiknode.pro
  http://ethers.avalanche-testnet.quiknode.pro
  http://ethers.blast-sepolia.quiknode.pro
  http://ethers.celo-mainnet.quiknode.pro
  http://ethers.fantom.quiknode.pro
  http://ethers.imx-demo.quiknode.pro
  http://ethers.imx-mainnet.quiknode.pro
  http://ethers.imx-testnet.quiknode.pro
  http://ethers.near-mainnet.quiknode.pro
  http://ethers.near-testnet.quiknode.pro
  http://ethers.nova-mainnet.quiknode.pro
  http://ethers.scroll-mainnet.quiknode.pro
  http://ethers.scroll-testnet.quiknode.pro
  http://ethers.tron-mainnet.quiknode.pro
  http://ethers.zkevm-mainnet.quiknode.pro
  http://ethers.zkevm-testnet.quiknode.pro
  http://ethers.zksync-mainnet.quiknode.pro
  http://ethers.zksync-testnet.quiknode.pro
*/



/**
 *  The **QuickNodeProvider** connects to the [[link-quicknode]]
 *  JSON-RPC end-points.
 *
 *  By default, a highly-throttled API token is used, which is
 *  appropriate for quick prototypes and simple scripts. To
 *  gain access to an increased rate-limit, it is highly
 *  recommended to [sign up here](link-quicknode).
 */
export class QuickNodeProvider extends JsonRpcProvider implements CommunityResourcable {
    /**
     *  The API token.
     */
    readonly token!: string;

    /**
     *  Creates a new **QuickNodeProvider**.
     */
    constructor(_network?: Networkish, token?: null | string) {
        if (_network == null) { _network = "mainnet"; }
        const network = Network.from(_network);
        if (token == null) { token = defaultToken; }

        const request = QuickNodeProvider.getRequest(network, token);
        super(request, network, { staticNetwork: network });

        defineProperties<QuickNodeProvider>(this, { token });
    }

    _getProvider(chainId: number): AbstractProvider {
        try {
            return new QuickNodeProvider(chainId, this.token);
        } catch (error) { }
        return super._getProvider(chainId);
    }

    isCommunityResource(): boolean {
        return (this.token === defaultToken);
    }

    /**
     *  Returns a new request prepared for %%network%% and the
     *  %%token%%.
     */
    static getRequest(network: Network, token?: null | string): FetchRequest {
        if (token == null) { token = defaultToken; }

        const request = new FetchRequest(`https:/\/${ getHost(network.name) }/${ token }`);
        request.allowGzip = true;
        //if (projectSecret) { request.setCredentials("", projectSecret); }

        if (token === defaultToken) {
            request.retryFunc = async (request, response, attempt) => {
                showThrottleMessage("QuickNodeProvider");
                return true;
            };
        }

        return request;
    }
}
