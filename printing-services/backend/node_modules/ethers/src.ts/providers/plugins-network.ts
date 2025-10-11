import { defineProperties } from "../utils/properties.js";

import { assertArgument } from "../utils/index.js";

import type { FeeData, Provider } from "./provider.js";
import type { FetchRequest } from "../utils/fetch.js";


const EnsAddress = "0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e";

/**
 *  A **NetworkPlugin** provides additional functionality on a [[Network]].
 */
export class NetworkPlugin {
    /**
     *  The name of the plugin.
     *
     *  It is recommended to use reverse-domain-notation, which permits
     *  unique names with a known authority as well as hierarchal entries.
     */
    readonly name!: string;

    /**
     *  Creates a new **NetworkPlugin**.
     */
    constructor(name: string) {
        defineProperties<NetworkPlugin>(this, { name });
    }

    /**
     *  Creates a copy of this plugin.
     */
    clone(): NetworkPlugin {
        return new NetworkPlugin(this.name);
    }

//    validate(network: Network): NetworkPlugin {
//        return this;
//    }
}


/**
 *  The gas cost parameters for a [[GasCostPlugin]].
 */
export type GasCostParameters = {
    /**
     *  The transactions base fee.
     */
    txBase?: number;

    /**
     *  The fee for creating a new account.
     */
    txCreate?: number;

    /**
     *  The fee per zero-byte in the data.
     */
    txDataZero?: number;

    /**
     *  The fee per non-zero-byte in the data.
     */
    txDataNonzero?: number;

    /**
     *  The fee per storage key in the [[link-eip-2930]] access list.
     */
    txAccessListStorageKey?: number;

    /**
     *  The fee per address in the [[link-eip-2930]] access list.
     */
    txAccessListAddress?: number;
};

/**
 *  A **GasCostPlugin** allows a network to provide alternative values when
 *  computing the intrinsic gas required for a transaction.
 */
export class GasCostPlugin extends NetworkPlugin implements GasCostParameters {
    /**
     *  The block number to treat these values as valid from.
     *
     *  This allows a hardfork to have updated values included as well as
     *  mulutiple hardforks to be supported.
     */
    readonly effectiveBlock!: number;

    /**
     *  The transactions base fee.
     */
    readonly txBase!: number;

    /**
     *  The fee for creating a new account.
     */
    readonly txCreate!: number;

    /**
     *  The fee per zero-byte in the data.
     */
    readonly txDataZero!: number;

    /**
     *  The fee per non-zero-byte in the data.
     */
    readonly txDataNonzero!: number;

    /**
     *  The fee per storage key in the [[link-eip-2930]] access list.
     */
    readonly txAccessListStorageKey!: number;

    /**
     *  The fee per address in the [[link-eip-2930]] access list.
     */
    readonly txAccessListAddress!: number;


    /**
     *  Creates a new GasCostPlugin from %%effectiveBlock%% until the
     *  latest block or another GasCostPlugin supercedes that block number,
     *  with the associated %%costs%%.
     */
    constructor(effectiveBlock?: number, costs?: GasCostParameters) {
        if (effectiveBlock == null) { effectiveBlock = 0; }
        super(`org.ethers.network.plugins.GasCost#${ (effectiveBlock || 0) }`);

        const props: Record<string, number> = { effectiveBlock };
        function set(name: keyof GasCostParameters, nullish: number): void {
            let value = (costs || { })[name];
            if (value == null) { value = nullish; }
            assertArgument(typeof(value) === "number", `invalud value for ${ name }`, "costs", costs);
            props[name] = value;
        }

        set("txBase", 21000);
        set("txCreate", 32000);
        set("txDataZero", 4);
        set("txDataNonzero", 16);
        set("txAccessListStorageKey", 1900);
        set("txAccessListAddress", 2400);

        defineProperties<GasCostPlugin>(this, props);
    }

    clone(): GasCostPlugin {
        return new GasCostPlugin(this.effectiveBlock, this);
    }
}

/**
 *  An **EnsPlugin** allows a [[Network]] to specify the ENS Registry
 *  Contract address and the target network to use when using that
 *  contract.
 *
 *  Various testnets have their own instance of the contract to use, but
 *  in general, the mainnet instance supports multi-chain addresses and
 *  should be used.
 */
export class EnsPlugin extends NetworkPlugin {

    /**
     *  The ENS Registrty Contract address.
     */
    readonly address!: string;

    /**
     *  The chain ID that the ENS contract lives on.
     */
    readonly targetNetwork!: number;

    /**
     *  Creates a new **EnsPlugin** connected to %%address%% on the
     *  %%targetNetwork%%. The default ENS address and mainnet is used
     *  if unspecified.
     */
    constructor(address?: null | string, targetNetwork?: null | number) {
        super("org.ethers.plugins.network.Ens");
        defineProperties<EnsPlugin>(this, {
            address: (address || EnsAddress),
            targetNetwork: ((targetNetwork == null) ? 1: targetNetwork)
        });
    }

    clone(): EnsPlugin {
        return new EnsPlugin(this.address, this.targetNetwork);
    }
}

/**
 *  A **FeeDataNetworkPlugin** allows a network to provide and alternate
 *  means to specify its fee data.
 *
 *  For example, a network which does not support [[link-eip-1559]] may
 *  choose to use a Gas Station site to approximate the gas price.
 */
export class FeeDataNetworkPlugin extends NetworkPlugin {
    readonly #feeDataFunc: (provider: Provider) => Promise<FeeData>;

    /**
     *  The fee data function provided to the constructor.
     */
    get feeDataFunc(): (provider: Provider) => Promise<FeeData> {
        return this.#feeDataFunc;
    }

    /**
     *  Creates a new **FeeDataNetworkPlugin**.
     */
    constructor(feeDataFunc: (provider: Provider) => Promise<FeeData>) {
        super("org.ethers.plugins.network.FeeData");
        this.#feeDataFunc = feeDataFunc;
    }

    /**
     *  Resolves to the fee data.
     */
    async getFeeData(provider: Provider): Promise<FeeData> {
        return await this.#feeDataFunc(provider);
    }

    clone(): FeeDataNetworkPlugin {
        return new FeeDataNetworkPlugin(this.#feeDataFunc);
    }
}

export class FetchUrlFeeDataNetworkPlugin extends NetworkPlugin {
    readonly #url: string;
    readonly #processFunc: (f: () => Promise<FeeData>, p: Provider, r: FetchRequest) => Promise<{ gasPrice?: null | bigint, maxFeePerGas?: null | bigint, maxPriorityFeePerGas?: null | bigint }>;

    /**
     *  The URL to initialize the FetchRequest with in %%processFunc%%.
     */
    get url(): string { return this.#url; }

    /**
     *  The callback to use when computing the FeeData.
     */
    get processFunc(): (f: () => Promise<FeeData>, p: Provider, r: FetchRequest) => Promise<{ gasPrice?: null | bigint, maxFeePerGas?: null | bigint, maxPriorityFeePerGas?: null | bigint }> { return this.#processFunc; }

    /**
     *  Creates a new **FetchUrlFeeDataNetworkPlugin** which will
     *  be used when computing the fee data for the network.
     */
    constructor(url: string, processFunc: (f: () => Promise<FeeData>, p: Provider, r: FetchRequest) => Promise<{ gasPrice?: null | bigint, maxFeePerGas?: null | bigint, maxPriorityFeePerGas?: null | bigint }>) {
        super("org.ethers.plugins.network.FetchUrlFeeDataPlugin");
        this.#url = url;
        this.#processFunc = processFunc;
    }

    // We are immutable, so we can serve as our own clone
    clone(): FetchUrlFeeDataNetworkPlugin { return this; }
}

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
