/**
 *  A **Network** encapsulates the various properties required to
 *  interact with a specific chain.
 *
 *  @_subsection: api/providers:Networks  [networks]
 */
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
    name?: string;
    chainId?: number;
    ensAddress?: string;
    ensNetwork?: number;
};
/**
 *  A **Network** provides access to a chain's properties and allows
 *  for plug-ins to extend functionality.
 */
export declare class Network {
    #private;
    /**
     *  Creates a new **Network** for %%name%% and %%chainId%%.
     */
    constructor(name: string, chainId: BigNumberish);
    /**
     *  Returns a JSON-compatible representation of a Network.
     */
    toJSON(): any;
    /**
     *  The network common name.
     *
     *  This is the canonical name, as networks migh have multiple
     *  names.
     */
    get name(): string;
    set name(value: string);
    /**
     *  The network chain ID.
     */
    get chainId(): bigint;
    set chainId(value: BigNumberish);
    /**
     *  Returns true if %%other%% matches this network. Any chain ID
     *  must match, and if no chain ID is present, the name must match.
     *
     *  This method does not currently check for additional properties,
     *  such as ENS address or plug-in compatibility.
     */
    matches(other: Networkish): boolean;
    /**
     *  Returns the list of plugins currently attached to this Network.
     */
    get plugins(): Array<NetworkPlugin>;
    /**
     *  Attach a new %%plugin%% to this Network. The network name
     *  must be unique, excluding any fragment.
     */
    attachPlugin(plugin: NetworkPlugin): this;
    /**
     *  Return the plugin, if any, matching %%name%% exactly. Plugins
     *  with fragments will not be returned unless %%name%% includes
     *  a fragment.
     */
    getPlugin<T extends NetworkPlugin = NetworkPlugin>(name: string): null | T;
    /**
     *  Gets a list of all plugins that match %%name%%, with otr without
     *  a fragment.
     */
    getPlugins<T extends NetworkPlugin = NetworkPlugin>(basename: string): Array<T>;
    /**
     *  Create a copy of this Network.
     */
    clone(): Network;
    /**
     *  Compute the intrinsic gas required for a transaction.
     *
     *  A GasCostPlugin can be attached to override the default
     *  values.
     */
    computeIntrinsicGas(tx: TransactionLike): number;
    /**
     *  Returns a new Network for the %%network%% name or chainId.
     */
    static from(network?: Networkish): Network;
    /**
     *  Register %%nameOrChainId%% with a function which returns
     *  an instance of a Network representing that chain.
     */
    static register(nameOrChainId: string | number | bigint, networkFunc: () => Network): void;
}
//# sourceMappingURL=network.d.ts.map