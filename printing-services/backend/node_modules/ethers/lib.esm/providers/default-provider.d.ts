import type { AbstractProvider } from "./abstract-provider.js";
import type { Networkish } from "./network.js";
import { WebSocketLike } from "./provider-websocket.js";
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
export declare function getDefaultProvider(network?: string | Networkish | WebSocketLike, options?: any): AbstractProvider;
//# sourceMappingURL=default-provider.d.ts.map