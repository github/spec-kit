"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FetchUrlFeeDataNetworkPlugin = exports.FeeDataNetworkPlugin = exports.EnsPlugin = exports.GasCostPlugin = exports.NetworkPlugin = void 0;
const properties_js_1 = require("../utils/properties.js");
const index_js_1 = require("../utils/index.js");
const EnsAddress = "0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e";
/**
 *  A **NetworkPlugin** provides additional functionality on a [[Network]].
 */
class NetworkPlugin {
    /**
     *  The name of the plugin.
     *
     *  It is recommended to use reverse-domain-notation, which permits
     *  unique names with a known authority as well as hierarchal entries.
     */
    name;
    /**
     *  Creates a new **NetworkPlugin**.
     */
    constructor(name) {
        (0, properties_js_1.defineProperties)(this, { name });
    }
    /**
     *  Creates a copy of this plugin.
     */
    clone() {
        return new NetworkPlugin(this.name);
    }
}
exports.NetworkPlugin = NetworkPlugin;
/**
 *  A **GasCostPlugin** allows a network to provide alternative values when
 *  computing the intrinsic gas required for a transaction.
 */
class GasCostPlugin extends NetworkPlugin {
    /**
     *  The block number to treat these values as valid from.
     *
     *  This allows a hardfork to have updated values included as well as
     *  mulutiple hardforks to be supported.
     */
    effectiveBlock;
    /**
     *  The transactions base fee.
     */
    txBase;
    /**
     *  The fee for creating a new account.
     */
    txCreate;
    /**
     *  The fee per zero-byte in the data.
     */
    txDataZero;
    /**
     *  The fee per non-zero-byte in the data.
     */
    txDataNonzero;
    /**
     *  The fee per storage key in the [[link-eip-2930]] access list.
     */
    txAccessListStorageKey;
    /**
     *  The fee per address in the [[link-eip-2930]] access list.
     */
    txAccessListAddress;
    /**
     *  Creates a new GasCostPlugin from %%effectiveBlock%% until the
     *  latest block or another GasCostPlugin supercedes that block number,
     *  with the associated %%costs%%.
     */
    constructor(effectiveBlock, costs) {
        if (effectiveBlock == null) {
            effectiveBlock = 0;
        }
        super(`org.ethers.network.plugins.GasCost#${(effectiveBlock || 0)}`);
        const props = { effectiveBlock };
        function set(name, nullish) {
            let value = (costs || {})[name];
            if (value == null) {
                value = nullish;
            }
            (0, index_js_1.assertArgument)(typeof (value) === "number", `invalud value for ${name}`, "costs", costs);
            props[name] = value;
        }
        set("txBase", 21000);
        set("txCreate", 32000);
        set("txDataZero", 4);
        set("txDataNonzero", 16);
        set("txAccessListStorageKey", 1900);
        set("txAccessListAddress", 2400);
        (0, properties_js_1.defineProperties)(this, props);
    }
    clone() {
        return new GasCostPlugin(this.effectiveBlock, this);
    }
}
exports.GasCostPlugin = GasCostPlugin;
/**
 *  An **EnsPlugin** allows a [[Network]] to specify the ENS Registry
 *  Contract address and the target network to use when using that
 *  contract.
 *
 *  Various testnets have their own instance of the contract to use, but
 *  in general, the mainnet instance supports multi-chain addresses and
 *  should be used.
 */
class EnsPlugin extends NetworkPlugin {
    /**
     *  The ENS Registrty Contract address.
     */
    address;
    /**
     *  The chain ID that the ENS contract lives on.
     */
    targetNetwork;
    /**
     *  Creates a new **EnsPlugin** connected to %%address%% on the
     *  %%targetNetwork%%. The default ENS address and mainnet is used
     *  if unspecified.
     */
    constructor(address, targetNetwork) {
        super("org.ethers.plugins.network.Ens");
        (0, properties_js_1.defineProperties)(this, {
            address: (address || EnsAddress),
            targetNetwork: ((targetNetwork == null) ? 1 : targetNetwork)
        });
    }
    clone() {
        return new EnsPlugin(this.address, this.targetNetwork);
    }
}
exports.EnsPlugin = EnsPlugin;
/**
 *  A **FeeDataNetworkPlugin** allows a network to provide and alternate
 *  means to specify its fee data.
 *
 *  For example, a network which does not support [[link-eip-1559]] may
 *  choose to use a Gas Station site to approximate the gas price.
 */
class FeeDataNetworkPlugin extends NetworkPlugin {
    #feeDataFunc;
    /**
     *  The fee data function provided to the constructor.
     */
    get feeDataFunc() {
        return this.#feeDataFunc;
    }
    /**
     *  Creates a new **FeeDataNetworkPlugin**.
     */
    constructor(feeDataFunc) {
        super("org.ethers.plugins.network.FeeData");
        this.#feeDataFunc = feeDataFunc;
    }
    /**
     *  Resolves to the fee data.
     */
    async getFeeData(provider) {
        return await this.#feeDataFunc(provider);
    }
    clone() {
        return new FeeDataNetworkPlugin(this.#feeDataFunc);
    }
}
exports.FeeDataNetworkPlugin = FeeDataNetworkPlugin;
class FetchUrlFeeDataNetworkPlugin extends NetworkPlugin {
    #url;
    #processFunc;
    /**
     *  The URL to initialize the FetchRequest with in %%processFunc%%.
     */
    get url() { return this.#url; }
    /**
     *  The callback to use when computing the FeeData.
     */
    get processFunc() { return this.#processFunc; }
    /**
     *  Creates a new **FetchUrlFeeDataNetworkPlugin** which will
     *  be used when computing the fee data for the network.
     */
    constructor(url, processFunc) {
        super("org.ethers.plugins.network.FetchUrlFeeDataPlugin");
        this.#url = url;
        this.#processFunc = processFunc;
    }
    // We are immutable, so we can serve as our own clone
    clone() { return this; }
}
exports.FetchUrlFeeDataNetworkPlugin = FetchUrlFeeDataNetworkPlugin;
/*
export class CustomBlockNetworkPlugin extends NetworkPlugin {
    readonly #blockFunc: (provider: Provider, block: BlockParams<string>) => Block<string>;
    readonly #blockWithTxsFunc: (provider: Provider, block: BlockParams<TransactionResponseParams>) => Block<TransactionResponse>;

    constructor(blockFunc: (provider: Provider, block: BlockParams<string>) => Block<string>, blockWithTxsFunc: (provider: Provider, block: BlockParams<TransactionResponseParams>) => Block<TransactionResponse>) {
        super("org.ethers.network-plugins.custom-block");
        this.#blockFunc = blockFunc;
        this.#blockWithTxsFunc = blockWithTxsFunc;
    }

    async getBlock(provider: Provider, block: BlockParams<string>): Promise<Block<string>> {
        return await this.#blockFunc(provider, block);
    }

    async getBlockions(provider: Provider, block: BlockParams<TransactionResponseParams>): Promise<Block<TransactionResponse>> {
        return await this.#blockWithTxsFunc(provider, block);
    }

    clone(): CustomBlockNetworkPlugin {
        return new CustomBlockNetworkPlugin(this.#blockFunc, this.#blockWithTxsFunc);
    }
}
*/
//# sourceMappingURL=plugins-network.js.map