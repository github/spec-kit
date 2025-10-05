/**
 *  Utilities for common tasks involving hashing. Also see
 *  [cryptographic hashing](about-crypto-hashing).
 *
 *  @_section: api/hashing:Hashing Utilities  [about-hashing]
 */

export { hashAuthorization, verifyAuthorization } from "./authorization.js";
export { id } from "./id.js"
export { ensNormalize, isValidName, namehash, dnsEncode } from "./namehash.js";
export { hashMessage, verifyMessage } from "./message.js";
export {
    solidityPacked, solidityPackedKeccak256, solidityPackedSha256
} from "./solidity.js";
export { TypedDataEncoder, verifyTypedData } from "./typed-data.js";

export type { AuthorizationRequest } from "./authorization.js";
export type { TypedDataDomain, TypedDataField } from "./typed-data.js";
