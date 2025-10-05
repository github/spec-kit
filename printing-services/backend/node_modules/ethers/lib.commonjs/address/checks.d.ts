import type { Addressable, AddressLike, NameResolver } from "./index.js";
/**
 *  Returns true if %%value%% is an object which implements the
 *  [[Addressable]] interface.
 *
 *  @example:
 *    // Wallets and AbstractSigner sub-classes
 *    isAddressable(Wallet.createRandom())
 *    //_result:
 *
 *    // Contracts
 *    contract = new Contract("dai.tokens.ethers.eth", [ ], provider)
 *    isAddressable(contract)
 *    //_result:
 */
export declare function isAddressable(value: any): value is Addressable;
/**
 *  Returns true if %%value%% is a valid address.
 *
 *  @example:
 *    // Valid address
 *    isAddress("0x8ba1f109551bD432803012645Ac136ddd64DBA72")
 *    //_result:
 *
 *    // Valid ICAP address
 *    isAddress("XE65GB6LDNXYOFTX0NSV3FUWKOWIXAMJK36")
 *    //_result:
 *
 *    // Invalid checksum
 *    isAddress("0x8Ba1f109551bD432803012645Ac136ddd64DBa72")
 *    //_result:
 *
 *    // Invalid ICAP checksum
 *    isAddress("0x8Ba1f109551bD432803012645Ac136ddd64DBA72")
 *    //_result:
 *
 *    // Not an address (an ENS name requires a provided and an
 *    // asynchronous API to access)
 *    isAddress("ricmoo.eth")
 *    //_result:
 */
export declare function isAddress(value: any): value is string;
/**
 *  Resolves to an address for the %%target%%, which may be any
 *  supported address type, an [[Addressable]] or a Promise which
 *  resolves to an address.
 *
 *  If an ENS name is provided, but that name has not been correctly
 *  configured a [[UnconfiguredNameError]] is thrown.
 *
 *  @example:
 *    addr = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
 *
 *    // Addresses are return synchronously
 *    resolveAddress(addr, provider)
 *    //_result:
 *
 *    // Address promises are resolved asynchronously
 *    resolveAddress(Promise.resolve(addr))
 *    //_result:
 *
 *    // ENS names are resolved asynchronously
 *    resolveAddress("dai.tokens.ethers.eth", provider)
 *    //_result:
 *
 *    // Addressable objects are resolved asynchronously
 *    contract = new Contract(addr, [ ])
 *    resolveAddress(contract, provider)
 *    //_result:
 *
 *    // Unconfigured ENS names reject
 *    resolveAddress("nothing-here.ricmoo.eth", provider)
 *    //_error:
 *
 *    // ENS names require a NameResolver object passed in
 *    // (notice the provider was omitted)
 *    resolveAddress("nothing-here.ricmoo.eth")
 *    //_error:
 */
export declare function resolveAddress(target: AddressLike, resolver?: null | NameResolver): string | Promise<string>;
//# sourceMappingURL=checks.d.ts.map