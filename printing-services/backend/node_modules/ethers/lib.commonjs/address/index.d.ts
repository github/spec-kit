/**
 *  Addresses are a fundamental part of interacting with Ethereum. They
 *  represent the global identity of Externally Owned Accounts (accounts
 *  backed by a private key) and contracts.
 *
 *  The Ethereum Naming Service (ENS) provides an interconnected ecosystem
 *  of contracts, standards and libraries which enable looking up an
 *  address for an ENS name.
 *
 *  These functions help convert between various formats, validate
 *  addresses and safely resolve ENS names.
 *
 *  @_section: api/address:Addresses  [about-addresses]
 */
/**
 *  An interface for objects which have an address, and can
 *  resolve it asyncronously.
 *
 *  This allows objects such as [[Signer]] or [[Contract]] to
 *  be used most places an address can be, for example getting
 *  the [balance](Provider-getBalance).
 */
export interface Addressable {
    /**
     *  Get the object address.
     */
    getAddress(): Promise<string>;
}
/**
 *  Anything that can be used to return or resolve an address.
 */
export type AddressLike = string | Promise<string> | Addressable;
/**
 *  An interface for any object which can resolve an ENS name.
 */
export interface NameResolver {
    /**
     *  Resolve to the address for the ENS %%name%%.
     *
     *  Resolves to ``null`` if the name is unconfigued. Use
     *  [[resolveAddress]] (passing this object as %%resolver%%) to
     *  throw for names that are unconfigured.
     */
    resolveName(name: string): Promise<null | string>;
}
export { getAddress, getIcapAddress } from "./address.js";
export { getCreateAddress, getCreate2Address } from "./contract-address.js";
export { isAddressable, isAddress, resolveAddress } from "./checks.js";
//# sourceMappingURL=index.d.ts.map