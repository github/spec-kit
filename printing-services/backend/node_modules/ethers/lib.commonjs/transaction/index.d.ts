/**
 *  Each state-changing operation on Ethereum requires a transaction.
 *
 *  @_section api/transaction:Transactions  [about-transactions]
 */
import type { BigNumberish } from "../utils/maths.js";
import type { Signature, SignatureLike } from "../crypto/index.js";
/**
 *  A single [[AccessList]] entry of storage keys (slots) for an address.
 */
export type AccessListEntry = {
    address: string;
    storageKeys: Array<string>;
};
/**
 *  An ordered collection of [[AccessList]] entries.
 */
export type AccessList = Array<AccessListEntry>;
/**
 *  Any ethers-supported access list structure.
 */
export type AccessListish = AccessList | Array<[string, Array<string>]> | Record<string, Array<string>>;
export interface Authorization {
    address: string;
    nonce: bigint;
    chainId: bigint;
    signature: Signature;
}
export type AuthorizationLike = {
    address: string;
    nonce: BigNumberish;
    chainId: BigNumberish;
    signature: SignatureLike;
};
export { accessListify } from "./accesslist.js";
export { authorizationify } from "./authorization.js";
export { computeAddress, recoverAddress } from "./address.js";
export { Transaction } from "./transaction.js";
export type { Blob, BlobLike, KzgLibrary, KzgLibraryLike, TransactionLike } from "./transaction.js";
//# sourceMappingURL=index.d.ts.map