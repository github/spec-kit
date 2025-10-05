/**
 *  ENS is a service which allows easy-to-remember names to map to
 *  network addresses.
 *
 *  @_section: api/providers/ens-resolver:ENS Resolver  [about-ens-rsolver]
 */
import type { BytesLike } from "../utils/index.js";
import type { AbstractProvider, AbstractProviderPlugin } from "./abstract-provider.js";
import type { Provider } from "./provider.js";
/**
 *  The type of data found during a steip during avatar resolution.
 */
export type AvatarLinkageType = "name" | "avatar" | "!avatar" | "url" | "data" | "ipfs" | "erc721" | "erc1155" | "!erc721-caip" | "!erc1155-caip" | "!owner" | "owner" | "!balance" | "balance" | "metadata-url-base" | "metadata-url-expanded" | "metadata-url" | "!metadata-url" | "!metadata" | "metadata" | "!imageUrl" | "imageUrl-ipfs" | "imageUrl" | "!imageUrl-ipfs";
/**
 *  An individual record for each step during avatar resolution.
 */
export interface AvatarLinkage {
    /**
     *  The type of linkage.
     */
    type: AvatarLinkageType;
    /**
     *  The linkage value.
     */
    value: string;
}
/**
 *  When resolving an avatar for an ENS name, there are many
 *  steps involved, fetching metadata, validating results, et cetera.
 *
 *  Some applications may wish to analyse this data, or use this data
 *  to diagnose promblems, so an **AvatarResult** provides details of
 *  each completed step during avatar resolution.
 */
export interface AvatarResult {
    /**
     *  How the [[url]] was arrived at, resolving the many steps required
     *  for an avatar URL.
     */
    linkage: Array<AvatarLinkage>;
    /**
     *  The avatar URL or null if the avatar was not set, or there was
     *  an issue during validation (such as the address not owning the
     *  avatar or a metadata error).
     */
    url: null | string;
}
/**
 *  A provider plugin super-class for processing multicoin address types.
 */
export declare abstract class MulticoinProviderPlugin implements AbstractProviderPlugin {
    /**
     *  The name.
     */
    readonly name: string;
    /**
     *  Creates a new **MulticoinProviderPluing** for %%name%%.
     */
    constructor(name: string);
    connect(proivder: Provider): MulticoinProviderPlugin;
    /**
     *  Returns ``true`` if %%coinType%% is supported by this plugin.
     */
    supportsCoinType(coinType: number): boolean;
    /**
     *  Resolves to the encoded %%address%% for %%coinType%%.
     */
    encodeAddress(coinType: number, address: string): Promise<string>;
    /**
     *  Resolves to the decoded %%data%% for %%coinType%%.
     */
    decodeAddress(coinType: number, data: BytesLike): Promise<string>;
}
/**
 *  A **BasicMulticoinProviderPlugin** provides service for common
 *  coin types, which do not require additional libraries to encode or
 *  decode.
 */
export declare class BasicMulticoinProviderPlugin extends MulticoinProviderPlugin {
    /**
     *  Creates a new **BasicMulticoinProviderPlugin**.
     */
    constructor();
}
/**
 *  A connected object to a resolved ENS name resolver, which can be
 *  used to query additional details.
 */
export declare class EnsResolver {
    #private;
    /**
     *  The connected provider.
     */
    provider: AbstractProvider;
    /**
     *  The address of the resolver.
     */
    address: string;
    /**
     *  The name this resolver was resolved against.
     */
    name: string;
    constructor(provider: AbstractProvider, address: string, name: string);
    /**
     *  Resolves to true if the resolver supports wildcard resolution.
     */
    supportsWildcard(): Promise<boolean>;
    /**
     *  Resolves to the address for %%coinType%% or null if the
     *  provided %%coinType%% has not been configured.
     */
    getAddress(coinType?: number): Promise<null | string>;
    /**
     *  Resolves to the EIP-634 text record for %%key%%, or ``null``
     *  if unconfigured.
     */
    getText(key: string): Promise<null | string>;
    /**
     *  Rsolves to the content-hash or ``null`` if unconfigured.
     */
    getContentHash(): Promise<null | string>;
    /**
     *  Resolves to the avatar url or ``null`` if the avatar is either
     *  unconfigured or incorrectly configured (e.g. references an NFT
     *  not owned by the address).
     *
     *  If diagnosing issues with configurations, the [[_getAvatar]]
     *  method may be useful.
     */
    getAvatar(): Promise<null | string>;
    /**
     *  When resolving an avatar, there are many steps involved, such
     *  fetching metadata and possibly validating ownership of an
     *  NFT.
     *
     *  This method can be used to examine each step and the value it
     *  was working from.
     */
    _getAvatar(): Promise<AvatarResult>;
    static getEnsAddress(provider: Provider): Promise<string>;
    /**
     *  Resolve to the ENS resolver for %%name%% using %%provider%% or
     *  ``null`` if unconfigured.
     */
    static fromName(provider: AbstractProvider, name: string): Promise<null | EnsResolver>;
}
//# sourceMappingURL=ens-resolver.d.ts.map