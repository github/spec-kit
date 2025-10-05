/**
 *  A **Network** encapsulates the various properties required to
 *  interact with a specific chain.
 *
 *  @_subsection: api/providers:Networks  [networks]
 */
import { accessListify } from "../transaction/index.js";
import { getBigInt, assert, assertArgument } from "../utils/index.js";
import { EnsPlugin, FetchUrlFeeDataNetworkPlugin, GasCostPlugin } from "./plugins-network.js";
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
const Networks = new Map();
/**
 *  A **Network** provides access to a chain's properties and allows
 *  for plug-ins to extend functionality.
 */
export class Network {
    #name;
    #chainId;
    #plugins;
    /**
     *  Creates a new **Network** for %%name%% and %%chainId%%.
     */
    constructor(name, chainId) {
        this.#name = name;
        this.#chainId = getBigInt(chainId);
        this.#plugins = new Map();
    }
    /**
     *  Returns a JSON-compatible representation of a Network.
     */
    toJSON() {
        return { name: this.name, chainId: String(this.chainId) };
    }
    /**
     *  The network common name.
     *
     *  This is the canonical name, as networks migh have multiple
     *  names.
     */
    get name() { return this.#name; }
    set name(value) { this.#name = value; }
    /**
     *  The network chain ID.
     */
    get chainId() { return this.#chainId; }
    set chainId(value) { this.#chainId = getBigInt(value, "chainId"); }
    /**
     *  Returns true if %%other%% matches this network. Any chain ID
     *  must match, and if no chain ID is present, the name must match.
     *
     *  This method does not currently check for additional properties,
     *  such as ENS address or plug-in compatibility.
     */
    matches(other) {
        if (other == null) {
            return false;
        }
        if (typeof (other) === "string") {
            try {
                return (this.chainId === getBigInt(other));
            }
            catch (error) { }
            return (this.name === other);
        }
        if (typeof (other) === "number" || typeof (other) === "bigint") {
            try {
                return (this.chainId === getBigInt(other));
            }
            catch (error) { }
            return false;
        }
        if (typeof (other) === "object") {
            if (other.chainId != null) {
                try {
                    return (this.chainId === getBigInt(other.chainId));
                }
                catch (error) { }
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
    get plugins() {
        return Array.from(this.#plugins.values());
    }
    /**
     *  Attach a new %%plugin%% to this Network. The network name
     *  must be unique, excluding any fragment.
     */
    attachPlugin(plugin) {
        if (this.#plugins.get(plugin.name)) {
            throw new Error(`cannot replace existing plugin: ${plugin.name} `);
        }
        this.#plugins.set(plugin.name, plugin.clone());
        return this;
    }
    /**
     *  Return the plugin, if any, matching %%name%% exactly. Plugins
     *  with fragments will not be returned unless %%name%% includes
     *  a fragment.
     */
    getPlugin(name) {
        return (this.#plugins.get(name)) || null;
    }
    /**
     *  Gets a list of all plugins that match %%name%%, with otr without
     *  a fragment.
     */
    getPlugins(basename) {
        return (this.plugins.filter((p) => (p.name.split("#")[0] === basename)));
    }
    /**
     *  Create a copy of this Network.
     */
    clone() {
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
    computeIntrinsicGas(tx) {
        const costs = this.getPlugin("org.ethers.plugins.network.GasCost") || (new GasCostPlugin());
        let gas = costs.txBase;
        if (tx.to == null) {
            gas += costs.txCreate;
        }
        if (tx.data) {
            for (let i = 2; i < tx.data.length; i += 2) {
                if (tx.data.substring(i, i + 2) === "00") {
                    gas += costs.txDataZero;
                }
                else {
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
    static from(network) {
        injectCommonNetworks();
        // Default network
        if (network == null) {
            return Network.from("mainnet");
        }
        // Canonical name or chain ID
        if (typeof (network) === "number") {
            network = BigInt(network);
        }
        if (typeof (network) === "string" || typeof (network) === "bigint") {
            const networkFunc = Networks.get(network);
            if (networkFunc) {
                return networkFunc();
            }
            if (typeof (network) === "bigint") {
                return new Network("unknown", network);
            }
            assertArgument(false, "unknown network", "network", network);
        }
        // Clonable with network-like abilities
        if (typeof (network.clone) === "function") {
            const clone = network.clone();
            //if (typeof(network.name) !== "string" || typeof(network.chainId) !== "number") {
            //}
            return clone;
        }
        // Networkish
        if (typeof (network) === "object") {
            assertArgument(typeof (network.name) === "string" && typeof (network.chainId) === "number", "invalid network object name or chainId", "network", network);
            const custom = new Network((network.name), (network.chainId));
            if (network.ensAddress || network.ensNetwork != null) {
                custom.attachPlugin(new EnsPlugin(network.ensAddress, network.ensNetwork));
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
    static register(nameOrChainId, networkFunc) {
        if (typeof (nameOrChainId) === "number") {
            nameOrChainId = BigInt(nameOrChainId);
        }
        const existing = Networks.get(nameOrChainId);
        if (existing) {
            assertArgument(false, `conflicting network for ${JSON.stringify(existing.name)}`, "nameOrChainId", nameOrChainId);
        }
        Networks.set(nameOrChainId, networkFunc);
    }
}
// We don't want to bring in formatUnits because it is backed by
// FixedNumber and we want to keep Networks tiny. The values
// included by the Gas Stations are also IEEE 754 with lots of
// rounding issues and exceed the strict checks formatUnits has.
function parseUnits(_value, decimals) {
    const value = String(_value);
    if (!value.match(/^[0-9.]+$/)) {
        throw new Error(`invalid gwei value: ${_value}`);
    }
    // Break into [ whole, fraction ]
    const comps = value.split(".");
    if (comps.length === 1) {
        comps.push("");
    }
    // More than 1 decimal point or too many fractional positions
    if (comps.length !== 2) {
        throw new Error(`invalid gwei value: ${_value}`);
    }
    // Pad the fraction to 9 decimalplaces
    while (comps[1].length < decimals) {
        comps[1] += "0";
    }
    // Too many decimals and some non-zero ending, take the ceiling
    if (comps[1].length > 9) {
        let frac = BigInt(comps[1].substring(0, 9));
        if (!comps[1].substring(9).match(/^0+$/)) {
            frac++;
        }
        comps[1] = frac.toString();
    }
    return BigInt(comps[0] + comps[1]);
}
// Used by Polygon to use a gas station for fee data
function getGasStationPlugin(url) {
    return new FetchUrlFeeDataNetworkPlugin(url, async (fetchFeeData, provider, request) => {
        // Prevent Cloudflare from blocking our request in node.js
        request.setHeader("User-Agent", "ethers");
        let response;
        try {
            const [_response, _feeData] = await Promise.all([
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
        }
        catch (error) {
            assert(false, `error encountered with polygon gas station (${JSON.stringify(request.url)})`, "SERVER_ERROR", { request, response, error });
        }
    });
}
// See: https://chainlist.org
let injected = false;
function injectCommonNetworks() {
    if (injected) {
        return;
    }
    injected = true;
    /// Register popular Ethereum networks
    function registerEth(name, chainId, options) {
        const func = function () {
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
    registerEth("mainnet", 1, { ensNetwork: 1, altNames: ["homestead"] });
    registerEth("ropsten", 3, { ensNetwork: 3 });
    registerEth("rinkeby", 4, { ensNetwork: 4 });
    registerEth("goerli", 5, { ensNetwork: 5 });
    registerEth("kovan", 42, { ensNetwork: 42 });
    registerEth("sepolia", 11155111, { ensNetwork: 11155111 });
    registerEth("holesky", 17000, { ensNetwork: 17000 });
    registerEth("classic", 61, {});
    registerEth("classicKotti", 6, {});
    registerEth("arbitrum", 42161, {
        ensNetwork: 1,
    });
    registerEth("arbitrum-goerli", 421613, {});
    registerEth("arbitrum-sepolia", 421614, {});
    registerEth("base", 8453, { ensNetwork: 1 });
    registerEth("base-goerli", 84531, {});
    registerEth("base-sepolia", 84532, {});
    registerEth("bnb", 56, { ensNetwork: 1 });
    registerEth("bnbt", 97, {});
    registerEth("linea", 59144, { ensNetwork: 1 });
    registerEth("linea-goerli", 59140, {});
    registerEth("linea-sepolia", 59141, {});
    registerEth("matic", 137, {
        ensNetwork: 1,
        plugins: [
            getGasStationPlugin("https:/\/gasstation.polygon.technology/v2")
        ]
    });
    registerEth("matic-amoy", 80002, {});
    registerEth("matic-mumbai", 80001, {
        altNames: ["maticMumbai", "maticmum"],
        plugins: [
            getGasStationPlugin("https:/\/gasstation-testnet.polygon.technology/v2")
        ]
    });
    registerEth("optimism", 10, {
        ensNetwork: 1,
        plugins: []
    });
    registerEth("optimism-goerli", 420, {});
    registerEth("optimism-sepolia", 11155420, {});
    registerEth("xdai", 100, { ensNetwork: 1 });
}
//# sourceMappingURL=network.js.map