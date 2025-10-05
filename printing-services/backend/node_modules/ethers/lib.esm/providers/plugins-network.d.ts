import type { FeeData, Provider } from "./provider.js";
import type { FetchRequest } from "../utils/fetch.js";
/**
 *  A **NetworkPlugin** provides additional functionality on a [[Network]].
 */
export declare class NetworkPlugin {
    /**
     *  The name of the plugin.
     *
     *  It is recommended to use reverse-domain-notation, which permits
     *  unique names with a known authority as well as hierarchal entries.
     */
    readonly name: string;
    /**
     *  Creates a new **NetworkPlugin**.
     */
    constructor(name: string);
    /**
     *  Creates a copy of this plugin.
     */
    clone(): NetworkPlugin;
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
export declare class GasCostPlugin extends NetworkPlugin implements GasCostParameters {
    /**
     *  The block number to treat these values as valid from.
     *
     *  This allows a hardfork to have updated values included as well as
     *  mulutiple hardforks to be supported.
     */
    readonly effectiveBlock: number;
    /**
     *  The transactions base fee.
     */
    readonly txBase: number;
    /**
     *  The fee for creating a new account.
     */
    readonly txCreate: number;
    /**
     *  The fee per zero-byte in the data.
     */
    readonly txDataZero: number;
    /**
     *  The fee per non-zero-byte in the data.
     */
    readonly txDataNonzero: number;
    /**
     *  The fee per storage key in the [[link-eip-2930]] access list.
     */
    readonly txAccessListStorageKey: number;
    /**
     *  The fee per address in the [[link-eip-2930]] access list.
     */
    readonly txAccessListAddress: number;
    /**
     *  Creates a new GasCostPlugin from %%effectiveBlock%% until the
     *  latest block or another GasCostPlugin supercedes that block number,
     *  with the associated %%costs%%.
     */
    constructor(effectiveBlock?: number, costs?: GasCostParameters);
    clone(): GasCostPlugin;
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
export declare class EnsPlugin extends NetworkPlugin {
    /**
     *  The ENS Registrty Contract address.
     */
    readonly address: string;
    /**
     *  The chain ID that the ENS contract lives on.
     */
    readonly targetNetwork: number;
    /**
     *  Creates a new **EnsPlugin** connected to %%address%% on the
     *  %%targetNetwork%%. The default ENS address and mainnet is used
     *  if unspecified.
     */
    constructor(address?: null | string, targetNetwork?: null | number);
    clone(): EnsPlugin;
}
/**
 *  A **FeeDataNetworkPlugin** allows a network to provide and alternate
 *  means to specify its fee data.
 *
 *  For example, a network which does not support [[link-eip-1559]] may
 *  choose to use a Gas Station site to approximate the gas price.
 */
export declare class FeeDataNetworkPlugin extends NetworkPlugin {
    #private;
    /**
     *  The fee data function provided to the constructor.
     */
    get feeDataFunc(): (provider: Provider) => Promise<FeeData>;
    /**
     *  Creates a new **FeeDataNetworkPlugin**.
     */
    constructor(feeDataFunc: (provider: Provider) => Promise<FeeData>);
    /**
     *  Resolves to the fee data.
     */
    getFeeData(provider: Provider): Promise<FeeData>;
    clone(): FeeDataNetworkPlugin;
}
export declare class FetchUrlFeeDataNetworkPlugin extends NetworkPlugin {
    #private;
    /**
     *  The URL to initialize the FetchRequest with in %%processFunc%%.
     */
    get url(): string;
    /**
     *  The callback to use when computing the FeeData.
     */
    get processFunc(): (f: () => Promise<FeeData>, p: Provider, r: FetchRequest) => Promise<{
        gasPrice?: null | bigint;
        maxFeePerGas?: null | bigint;
        maxPriorityFeePerGas?: null | bigint;
    }>;
    /**
     *  Creates a new **FetchUrlFeeDataNetworkPlugin** which will
     *  be used when computing the fee data for the network.
     */
    constructor(url: string, processFunc: (f: () => Promise<FeeData>, p: Provider, r: FetchRequest) => Promise<{
        gasPrice?: null | bigint;
        maxFeePerGas?: null | bigint;
        maxPriorityFeePerGas?: null | bigint;
    }>);
    clone(): FetchUrlFeeDataNetworkPlugin;
}
//# sourceMappingURL=plugins-network.d.ts.map