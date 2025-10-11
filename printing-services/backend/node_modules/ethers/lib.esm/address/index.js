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
null;
export { getAddress, getIcapAddress } from "./address.js";
export { getCreateAddress, getCreate2Address } from "./contract-address.js";
export { isAddressable, isAddress, resolveAddress } from "./checks.js";
//# sourceMappingURL=index.js.map