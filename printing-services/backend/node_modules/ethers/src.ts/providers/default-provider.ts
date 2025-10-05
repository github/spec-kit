
import { assert } from "../utils/index.js";

import { AnkrProvider } from "./provider-ankr.js";
import { AlchemyProvider } from "./provider-alchemy.js";
//import { BlockscoutProvider } from "./provider-blockscout.js";
import { ChainstackProvider } from "./provider-chainstack.js";
import { CloudflareProvider } from "./provider-cloudflare.js";
import { EtherscanProvider } from "./provider-etherscan.js";
import { InfuraProvider } from "./provider-infura.js";
//import { PocketProvider } from "./provider-pocket.js";
import { QuickNodeProvider } from "./provider-quicknode.js";

import { FallbackProvider } from "./provider-fallback.js";
import { JsonRpcProvider } from "./provider-jsonrpc.js";
import { Network } from "./network.js";
import { WebSocketProvider } from "./provider-websocket.js";

import type { AbstractProvider } from "./abstract-provider.js";
import type { Networkish } from "./network.js";
import { WebSocketLike } from "./provider-websocket.js";

function isWebSocketLike(value: any): value is WebSocketLike {
    return (value && typeof(value.send) === "function" &&
        typeof(value.close) === "function");
}

const Testnets = "goerli kovan sepolia classicKotti optimism-goerli arbitrum-goerli matic-mumbai bnbt".split(" ");

/**
 *  Returns a default provider for %%network%%.
 *
 *  If %%network%% is a [[WebSocketLike]] or string that begins with
 *  ``"ws:"`` or ``"wss:"``, a [[WebSocketProvider]] is returned backed
 *  by that WebSocket or URL.
 *
 *  If %%network%% is a string that begins with ``"HTTP:"`` or ``"HTTPS:"``,
 *  a [[JsonRpcProvider]] is returned connected to that URL.
 *
 *  Otherwise, a default provider is created backed by well-known public
 *  Web3 backends (such as [[link-infura]]) using community-provided API
 *  keys.
 *
 *  The %%options%% allows specifying custom API keys per backend (setting
 *  an API key to ``"-"`` will omit that provider) and ``options.exclusive``
 *  can be set to either a backend name or and array of backend names, which
 *  will whitelist **only** those backends.
 *
 *  Current backend strings supported are:
 *  - ``"alchemy"``
 *  - ``"ankr"``
 *  - ``"cloudflare"``
 *  - ``"chainstack"``
 *  - ``"etherscan"``
 *  - ``"infura"``
 *  - ``"publicPolygon"``
 *  - ``"quicknode"``
 *
 *  @example:
 *    // Connect to a local Geth node
 *    provider = getDefaultProvider("http://localhost:8545/");
 *
 *    // Connect to Ethereum mainnet with any current and future
 *    // third-party services available
 *    provider = getDefaultProvider("mainnet");
 *
 *    // Connect to Polygon, but only allow Etherscan and
 *    // INFURA and use "MY_API_KEY" in calls to Etherscan.
 *    provider = getDefaultProvider("matic", {
 *      etherscan: "MY_API_KEY",
 *      exclusive: [ "etherscan", "infura" ]
 *    });
 */
export function getDefaultProvider(network?: string | Networkish | WebSocketLike, options?: any): AbstractProvider {
    if (options == null) { options = { }; }

    const allowService = (name: string) => {
        if (options[name] === "-") { return false; }
        if (typeof(options.exclusive) === "string") {
            return (name === options.exclusive);
        }
        if (Array.isArray(options.exclusive)) {
            return (options.exclusive.indexOf(name) !== -1);
        }
        return true;
    };

    if (typeof(network) === "string" && network.match(/^https?:/)) {
        return new JsonRpcProvider(network);
    }

    if (typeof(network) === "string" && network.match(/^wss?:/) || isWebSocketLike(network)) {
        return new WebSocketProvider(network);
    }

    // Get the network and name, if possible
    let staticNetwork: null | Network = null;
    try {
        staticNetwork = Network.from(network);
    } catch (error) { }


    const providers: Array<AbstractProvider> = [ ];

    if (allowService("publicPolygon") && staticNetwork) {
        if (staticNetwork.name === "matic") {
            providers.push(new JsonRpcProvider("https:/\/polygon-rpc.com/", staticNetwork, { staticNetwork }));
        } else if (staticNetwork.name === "matic-amoy") {
            providers.push(new JsonRpcProvider("https:/\/rpc-amoy.polygon.technology/", staticNetwork, { staticNetwork }));
        }
    }

    if (allowService("alchemy")) {
        try {
            providers.push(new AlchemyProvider(network, options.alchemy));
        } catch (error) { }
    }

    if (allowService("ankr") && options.ankr != null) {
        try {
            providers.push(new AnkrProvider(network, options.ankr));
        } catch (error) { }
    }
/* Temporarily remove until custom error issue is fixed
    if (allowService("blockscout")) {
        try {
            providers.push(new BlockscoutProvider(network, options.blockscout));
        } catch (error) { }
    }
*/
    if (allowService("chainstack")) {
        try {
            providers.push(new ChainstackProvider(network, options.chainstack));
        } catch (error) { }
    }

    if (allowService("cloudflare")) {
        try {
            providers.push(new CloudflareProvider(network));
        } catch (error) { }
    }

    if (allowService("etherscan")) {
        try {
            providers.push(new EtherscanProvider(network, options.etherscan));
        } catch (error) { }
    }

    if (allowService("infura")) {
        try {
            let projectId = options.infura;
            let projectSecret: undefined | string = undefined;
            if (typeof(projectId) === "object") {
                projectSecret = projectId.projectSecret;
                projectId = projectId.projectId;
            }
            providers.push(new InfuraProvider(network, projectId, projectSecret));
        } catch (error) { }
    }
/*
    if (options.pocket !== "-") {
        try {
            let appId = options.pocket;
            let secretKey: undefined | string = undefined;
            let loadBalancer: undefined | boolean = undefined;
            if (typeof(appId) === "object") {
                loadBalancer = !!appId.loadBalancer;
                secretKey = appId.secretKey;
                appId = appId.appId;
            }
            providers.push(new PocketProvider(network, appId, secretKey, loadBalancer));
        } catch (error) { console.log(error); }
    }
*/
    if (allowService("quicknode")) {
        try {
            let token = options.quicknode;
            providers.push(new QuickNodeProvider(network, token));
        } catch (error) { }
    }

    assert(providers.length, "unsupported default network", "UNSUPPORTED_OPERATION", {
        operation: "getDefaultProvider"
    });

    // No need for a FallbackProvider
    if (providers.length === 1) { return providers[0]; }

    // We use the floor because public third-party providers can be unreliable,
    // so a low number of providers with a large quorum will fail too often
    let quorum = Math.floor(providers.length / 2);
    if (quorum > 2) { quorum = 2; }

    // Testnets don't need as strong a security gaurantee and speed is
    // more useful during testing
    if (staticNetwork && Testnets.indexOf(staticNetwork.name) !== -1) { quorum = 1; }

    // Provided override qorum takes priority
    if (options && options.quorum) { quorum = options.quorum; }

    return new FallbackProvider(providers, undefined, { quorum });
}
