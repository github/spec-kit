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

import {
    defineProperties, resolveProperties, assert, assertArgument,
    FetchRequest
} from "../utils/index.js";

import { showThrottleMessage } from "./community.js";
import { Network } from "./network.js";
import { JsonRpcProvider } from "./provider-jsonrpc.js";

import type { AbstractProvider, PerformActionRequest } from "./abstract-provider.js";
import type { CommunityResourcable } from "./community.js";
import type { Networkish } from "./network.js";


const defaultApiKey = "_gg7wSSi0KMBsdKnGVfHDueq6xMB9EkC"

function getHost(name: string): string {
    switch(name) {
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

    assertArgument(false, "unsupported network", "network", name);
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
export class AlchemyProvider extends JsonRpcProvider implements CommunityResourcable {
    readonly apiKey!: string;

    constructor(_network?: Networkish, apiKey?: null | string) {
        if (_network == null) { _network = "mainnet"; }
        const network = Network.from(_network);
        if (apiKey == null) { apiKey = defaultApiKey; }

        const request = AlchemyProvider.getRequest(network, apiKey);
        super(request, network, { staticNetwork: network });

        defineProperties<AlchemyProvider>(this, { apiKey });
    }

    _getProvider(chainId: number): AbstractProvider {
        try {
            return new AlchemyProvider(chainId, this.apiKey);
        } catch (error) { }
        return super._getProvider(chainId);
    }

    async _perform(req: PerformActionRequest): Promise<any> {

        // https://docs.alchemy.com/reference/trace-transaction
        if (req.method === "getTransactionResult") {
            const { trace, tx } = await resolveProperties({
                trace: this.send("trace_transaction", [ req.hash ]),
                tx: this.getTransaction(req.hash)
            });
            if (trace == null || tx == null) { return null; }

            let data: undefined | string;
            let error = false;
            try {
                data = trace[0].result.output;
                error = (trace[0].error === "Reverted");
            } catch (error) { }

            if (data) {
                assert(!error, "an error occurred during transaction executions", "CALL_EXCEPTION", {
                    action: "getTransactionResult",
                    data,
                    reason: null,
                    transaction: tx,
                    invocation: null,
                    revert: null // @TODO
                });
                return data;
            }

            assert(false, "could not parse trace result", "BAD_DATA", { value: trace });
        }

        return await super._perform(req);
    }

    isCommunityResource(): boolean {
        return (this.apiKey === defaultApiKey);
    }

    static getRequest(network: Network, apiKey?: string): FetchRequest {
        if (apiKey == null) { apiKey = defaultApiKey; }

        const request = new FetchRequest(`https:/\/${ getHost(network.name) }/v2/${ apiKey }`);
        request.allowGzip = true;

        if (apiKey === defaultApiKey) {
            request.retryFunc = async (request, response, attempt) => {
                showThrottleMessage("alchemy");
                return true;
            }
        }

        return request;
    }
}
