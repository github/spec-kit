/**
 *  A **Network** encapsulates the various properties required to
 *  interact with a specific chain.
 *
 *  @_subsection: api/providers:Networks  [networks]
 */

import { accessListify } from "../transaction/index.js";
import { getBigInt, assert, assertArgument } from "../utils/index.js";

import {
    EnsPlugin, FetchUrlFeeDataNetworkPlugin, GasCostPlugin
} from "./plugins-network.js";

import type { BigNumberish } from "../utils/index.js";
import type { TransactionLike } from "../transaction/index.js";

import type { NetworkPlugin } from "./plugins-network.js";


/**
 *  A Networkish can be used to allude to a Network, by specifing:
 *  - a [[Network]] object
 *  - a well-known (or registered) network name
 *  - a well-known (or registered) chain ID
 *  - an object with sufficient details to describe a network
 */
export type Networkish = Network | number | bigint | string | {
    name?: string,
    chainId?: number,
    //layerOneConnection?: Provider,
    ensAddress?: string,
    ensNetwork?: number
};




/* * * *
// Networks which operation against an L2 can use this plugin to
// specify how to access L1, for the purpose of resolving ENS,
// for example.
export class LayerOneConnectionPlugin extends NetworkPlugin {
    readonly provider!: Provider;
// @TODO: Rename to ChainAccess and allow for connecting to any chain
    constructor(provider: Provider) {
        super("org.ethers.plugins.layer-one-connection");
        defineProperties<LayerOneConnectionPlugin>(this, { provider });
    }

    clone(): LayerOneConnectionPlugin {
        return new LayerOneConnectionPlugin(this.provider);
    }
}
*/


const Networks: Map<string | bigint, () => Network> = new Map();


/**
 *  A **Network** provides access to a chain's properties and allows
 *  for plug-ins to extend functionality.
 */
export class Network {
    #name: string;
    #chainId: bigint;

    #plugins: Map<string, NetworkPlugin>;

    /**
     *  Creates a new **Network** for %%name%% and %%chainId%%.
     */
    constructor(name: string, chainId: BigNumberish) {
        this.#name = name;
        this.#chainId = getBigInt(chainId);
        this.#plugins = new Map();
    }

    /**
     *  Returns a JSON-compatible representation of a Network.
     */
    toJSON(): any {
        return { name: this.name, chainId: String(this.chainId) };
    }

    /**
     *  The network common name.
     *
     *  This is the canonical name, as networks migh have multiple
     *  names.
     */
    get name(): string { return this.#name; }
    set name(value: string) { this.#name =  value; }

    /**
     *  The network chain ID.
     */
    get chainId(): bigint { return this.#chainId; }
    set chainId(value: BigNumberish) { this.#chainId = getBigInt(value, "chainId"); }

    /**
     *  Returns true if %%other%% matches this network. Any chain ID
     *  must match, and if no chain ID is present, the name must match.
     *
     *  This method does not currently check for additional properties,
     *  such as ENS address or plug-in compatibility.
     */
    matches(other: Networkish): boolean {
        if (other == null) { return false; }

        if (typeof(other) === "string") {
            try {
                return (this.chainId === getBigInt(other));
            } catch (error) { }
            return (this.name === other);
        }

        if (typeof(other) === "number" || typeof(other) === "bigint") {
            try {
                return (this.chainId === getBigInt(other));
            } catch (error) { }
            return false;
        }

        if (typeof(other) === "object") {
            if (other.chainId != null) {
                try {
                    return (this.chainId === getBigInt(other.chainId));
                } catch (error) { }
                return false;
            }
            if (other.name != null) {
                return (this.name === other.name);
            }
            return false;
        }

        return false;
    }

    /**
     *  Returns the list of plugins currently attached to this Network.
     */
    get plugins(): Array<NetworkPlugin> {
        return Array.from(this.#plugins.values());
    }

    /**
     *  Attach a new %%plugin%% to this Network. The network name
     *  must be unique, excluding any fragment.
     */
    attachPlugin(plugin: NetworkPlugin): this {
        if (this.#plugins.get(plugin.name)) {
            throw new Error(`cannot replace existing plugin: ${ plugin.name } `);
        }
        this.#plugins.set(plugin.name, plugin.clone());
        return this;
    }

    /**
     *  Return the plugin, if any, matching %%name%% exactly. Plugins
     *  with fragments will not be returned unless %%name%% includes
     *  a fragment.
     */
    getPlugin<T extends NetworkPlugin = NetworkPlugin>(name: string): null | T {
        return <T>(this.#plugins.get(name)) || null;
    }

    /**
     *  Gets a list of all plugins that match %%name%%, with otr without
     *  a fragment.
     */
    getPlugins<T extends NetworkPlugin = NetworkPlugin>(basename: string): Array<T> {
        return <Array<T>>(this.plugins.filter((p) => (p.name.split("#")[0] === basename)));
    }

    /**
     *  Create a copy of this Network.
     */
    clone(): Network {
        const clone = new Network(this.name, this.chainId);
        this.plugins.forEach((plugin) => {
            clone.attachPlugin(plugin.clone());
        });
        return clone;
    }

    /**
     *  Compute the intrinsic gas required for a transaction.
     *
     *  A GasCostPlugin can be attached to override the default
     *  values.
     */
    computeIntrinsicGas(tx: TransactionLike): number {
        const costs = this.getPlugin<GasCostPlugin>("org.ethers.plugins.network.GasCost") || (new GasCostPlugin());

        let gas = costs.txBase;
        if (tx.to == null) { gas += costs.txCreate; }
        if (tx.data) {
            for (let i = 2; i < tx.data.length; i += 2) {
                if (tx.data.substring(i, i + 2) === "00") {
                    gas += costs.txDataZero;
                } else {
                    gas += costs.txDataNonzero;
                }
            }
        }

        if (tx.accessList) {
            const accessList = accessListify(tx.accessList);
            for (const addr in accessList) {
                gas += costs.txAccessListAddress + costs.txAccessListStorageKey * accessList[addr].storageKeys.length;
            }
        }

        return gas;
    }

    /**
     *  Returns a new Network for the %%network%% name or chainId.
     */
    static from(network?: Networkish): Network {
        injectCommonNetworks();

        // Default network
        if (network == null) { return Network.from("mainnet"); }

        // Canonical name or chain ID
        if (typeof(network) === "number") { network = BigInt(network); }
        if (typeof(network) === "string" || typeof(network) === "bigint") {
            const networkFunc = Networks.get(network);
            if (networkFunc) { return networkFunc(); }
            if (typeof(network) === "bigint") {
                return new Network("unknown", network);
            }

            assertArgument(false, "unknown network", "network", network);
        }

        // Clonable with network-like abilities
        if (typeof((<Network>network).clone) === "function") {
            const clone = (<Network>network).clone();
            //if (typeof(network.name) !== "string" || typeof(network.chainId) !== "number") {
            //}
            return clone;
        }

        // Networkish
        if (typeof(network) === "object") {
            assertArgument(typeof(network.name) === "string" && typeof(network.chainId) === "number",
                "invalid network object name or chainId", "network", network);

            const custom = new Network(<string>(network.name), <number>(network.chainId));

            if ((<any>network).ensAddress || (<any>network).ensNetwork != null) {
                custom.attachPlugin(new EnsPlugin((<any>network).ensAddress, (<any>network).ensNetwork));
            }

            //if ((<any>network).layerOneConnection) {
            //    custom.attachPlugin(new LayerOneConnectionPlugin((<any>network).layerOneConnection));
            //}

            return custom;
        }

        assertArgument(false, "invalid network", "network", network);
    }

    /**
     *  Register %%nameOrChainId%% with a function which returns
     *  an instance of a Network representing that chain.
     */
    static register(nameOrChainId: string | number | bigint, networkFunc: () => Network): void {
        if (typeof(nameOrChainId) === "number") { nameOrChainId = BigInt(nameOrChainId); }
        const existing = Networks.get(nameOrChainId);
        if (existing) {
            assertArgument(false, `conflicting network for ${ JSON.stringify(existing.name) }`, "nameOrChainId", nameOrChainId);
        }
        Networks.set(nameOrChainId, networkFunc);
    }
}


type Options = {
    ensNetwork?: number;
    altNames?: Array<string>;
    plugins?: Array<NetworkPlugin>;
};

// We don't want to bring in formatUnits because it is backed by
// FixedNumber and we want to keep Networks tiny. The values
// included by the Gas Stations are also IEEE 754 with lots of
// rounding issues and exceed the strict checks formatUnits has.
function parseUnits(_value: number | string, decimals: number): bigint {
    const value = String(_value);
    if (!value.match(/^[0-9.]+$/)) {
        throw new Error(`invalid gwei value: ${ _value }`);
    }

    // Break into [ whole, fraction ]
    const comps = value.split(".");
    if (comps.length === 1) { comps.push(""); }

    // More than 1 decimal point or too many fractional positions
    if (comps.length !== 2) {
        throw new Error(`invalid gwei value: ${ _value }`);
    }

    // Pad the fraction to 9 decimalplaces
    while (comps[1].length < decimals) { comps[1] += "0"; }

    // Too many decimals and some non-zero ending, take the ceiling
    if (comps[1].length > 9) {
        let frac = BigInt(comps[1].substring(0, 9));
        if (!comps[1].substring(9).match(/^0+$/)) { frac++; }
        comps[1] = frac.toString();
    }

    return BigInt(comps[0] + comps[1]);
}

// Used by Polygon to use a gas station for fee data
function getGasStationPlugin(url: string) {
    return new FetchUrlFeeDataNetworkPlugin(url, async (fetchFeeData, provider, request) => {

        // Prevent Cloudflare from blocking our request in node.js
        request.setHeader("User-Agent", "ethers");

        let response;
        try {
            const [ _response, _feeData ] = await Promise.all([
                request.send(), fetchFeeData()
            ]);
            response = _response;
            const payload = response.bodyJson.standard;
            const feeData = {
                gasPrice: _feeData.gasPrice,
                maxFeePerGas: parseUnits(payload.maxFee, 9),
                maxPriorityFeePerGas: parseUnits(payload.maxPriorityFee, 9),
            };
            return feeData;
        } catch (error: any) {
            assert(false, `error encountered with polygon gas station (${ JSON.stringify(request.url) })`, "SERVER_ERROR", { request, response, error });
        }
    });
}

// See: https://chainlist.org
let injected = false;
function injectCommonNetworks(): void {
    if (injected) { return; }
    injected = true;

    /// Register popular Ethereum networks
    function registerEth(name: string, chainId: number, options: Options): void {
        const func = function() {
            const network = new Network(name, chainId);

            // We use 0 to disable ENS
            if (options.ensNetwork != null) {
                network.attachPlugin(new EnsPlugin(null, options.ensNetwork));
            }

            network.attachPlugin(new GasCostPlugin());

            (options.plugins || []).forEach((plugin) => {
                network.attachPlugin(plugin);
            });

            return network;
        };

        // Register the network by name and chain ID
        Network.register(name, func);
        Network.register(chainId, func);

        if (options.altNames) {
            options.altNames.forEach((name) => {
                Network.register(name, func);
            });
        }
    }

    registerEth("mainnet", 1, { ensNetwork: 1, altNames: [ "homestead" ] });
    registerEth("ropsten", 3, { ensNetwork: 3 });
    registerEth("rinkeby", 4, { ensNetwork: 4 });
    registerEth("goerli", 5, { ensNetwork: 5 });
    registerEth("kovan", 42, { ensNetwork: 42 });
    registerEth("sepolia", 11155111, { ensNetwork: 11155111 });
    registerEth("holesky", 17000, { ensNetwork: 17000 });

    registerEth("classic", 61, { });
    registerEth("classicKotti", 6, { });

    registerEth("arbitrum", 42161, {
        ensNetwork: 1,
    });
    registerEth("arbitrum-goerli", 421613, { });
    registerEth("arbitrum-sepolia", 421614, { });

    registerEth("base", 8453, { ensNetwork: 1 });
    registerEth("base-goerli", 84531, { });
    registerEth("base-sepolia", 84532, { });

    registerEth("bnb", 56, { ensNetwork: 1 });
    registerEth("bnbt", 97, { });

    registerEth("linea", 59144, { ensNetwork: 1 });
    registerEth("linea-goerli", 59140, { });
    registerEth("linea-sepolia", 59141, { });

    registerEth("matic", 137, {
        ensNetwork: 1,
        plugins: [
            getGasStationPlugin("https:/\/gasstation.polygon.technology/v2")
        ]
    });
    registerEth("matic-amoy", 80002, { });
    registerEth("matic-mumbai", 80001, {
        altNames: [ "maticMumbai", "maticmum" ],  // @TODO: Future remove these alts
        plugins: [
            getGasStationPlugin("https:/\/gasstation-testnet.polygon.technology/v2")
        ]
    });

    registerEth("optimism", 10, {
        ensNetwork: 1,
        plugins: [ ]
    });
    registerEth("optimism-goerli", 420, { });
    registerEth("optimism-sepolia", 11155420, { });

    registerEth("xdai", 100, { ensNetwork: 1 });
}
