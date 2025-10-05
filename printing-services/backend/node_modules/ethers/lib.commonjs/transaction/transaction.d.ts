import { Signature } from "../crypto/index.js";
import type { BigNumberish, BytesLike } from "../utils/index.js";
import type { SignatureLike } from "../crypto/index.js";
import type { AccessList, AccessListish, Authorization, AuthorizationLike } from "./index.js";
/**
 *  A **TransactionLike** is an object which is appropriate as a loose
 *  input for many operations which will populate missing properties of
 *  a transaction.
 */
export interface TransactionLike<A = string> {
    /**
     *  The type.
     */
    type?: null | number;
    /**
     *  The recipient address or ``null`` for an ``init`` transaction.
     */
    to?: null | A;
    /**
     *  The sender.
     */
    from?: null | A;
    /**
     *  The nonce.
     */
    nonce?: null | number;
    /**
     *  The maximum amount of gas that can be used.
     */
    gasLimit?: null | BigNumberish;
    /**
     *  The gas price for legacy and berlin transactions.
     */
    gasPrice?: null | BigNumberish;
    /**
     *  The maximum priority fee per gas for london transactions.
     */
    maxPriorityFeePerGas?: null | BigNumberish;
    /**
     *  The maximum total fee per gas for london transactions.
     */
    maxFeePerGas?: null | BigNumberish;
    /**
     *  The data.
     */
    data?: null | string;
    /**
     *  The value (in wei) to send.
     */
    value?: null | BigNumberish;
    /**
     *  The chain ID the transaction is valid on.
     */
    chainId?: null | BigNumberish;
    /**
     *  The transaction hash.
     */
    hash?: null | string;
    /**
     *  The signature provided by the sender.
     */
    signature?: null | SignatureLike;
    /**
     *  The access list for berlin and london transactions.
     */
    accessList?: null | AccessListish;
    /**
     *  The maximum fee per blob gas (see [[link-eip-4844]]).
     */
    maxFeePerBlobGas?: null | BigNumberish;
    /**
     *  The versioned hashes (see [[link-eip-4844]]).
     */
    blobVersionedHashes?: null | Array<string>;
    /**
     *  The blobs (if any) attached to this transaction (see [[link-eip-4844]]).
     */
    blobs?: null | Array<BlobLike>;
    /**
     *  An external library for computing the KZG commitments and
     *  proofs necessary for EIP-4844 transactions (see [[link-eip-4844]]).
     *
     *  This is generally ``null``, unless you are creating BLOb
     *  transactions.
     */
    kzg?: null | KzgLibraryLike;
    /**
     *  The [[link-eip-7702]] authorizations (if any).
     */
    authorizationList?: null | Array<Authorization>;
}
/**
 *  A full-valid BLOb object for [[link-eip-4844]] transactions.
 *
 *  The commitment and proof should have been computed using a
 *  KZG library.
 */
export interface Blob {
    data: string;
    proof: string;
    commitment: string;
}
/**
 *  A BLOb object that can be passed for [[link-eip-4844]]
 *  transactions.
 *
 *  It may have had its commitment and proof already provided
 *  or rely on an attached [[KzgLibrary]] to compute them.
 */
export type BlobLike = BytesLike | {
    data: BytesLike;
    proof: BytesLike;
    commitment: BytesLike;
};
/**
 *  A KZG Library with the necessary functions to compute
 *  BLOb commitments and proofs.
 */
export interface KzgLibrary {
    blobToKzgCommitment: (blob: Uint8Array) => Uint8Array;
    computeBlobKzgProof: (blob: Uint8Array, commitment: Uint8Array) => Uint8Array;
}
/**
 *  A KZG Library with any of the various API configurations.
 *  As the library is still experimental and the API is not
 *  stable, depending on the version used the method names and
 *  signatures are still in flux.
 *
 *  This allows any of the versions to be passed into Transaction
 *  while providing a stable external API.
 */
export type KzgLibraryLike = KzgLibrary | {
    blobToKZGCommitment: (blob: string) => string;
    computeBlobKZGProof: (blob: string, commitment: string) => string;
} | {
    blobToKzgCommitment: (blob: string) => string | Uint8Array;
    computeBlobProof: (blob: string, commitment: string) => string | Uint8Array;
};
/**
 *  A **Transaction** describes an operation to be executed on
 *  Ethereum by an Externally Owned Account (EOA). It includes
 *  who (the [[to]] address), what (the [[data]]) and how much (the
 *  [[value]] in ether) the operation should entail.
 *
 *  @example:
 *    tx = new Transaction()
 *    //_result:
 *
 *    tx.data = "0x1234";
 *    //_result:
 */
export declare class Transaction implements TransactionLike<string> {
    #private;
    /**
     *  The transaction type.
     *
     *  If null, the type will be automatically inferred based on
     *  explicit properties.
     */
    get type(): null | number;
    set type(value: null | number | string);
    /**
     *  The name of the transaction type.
     */
    get typeName(): null | string;
    /**
     *  The ``to`` address for the transaction or ``null`` if the
     *  transaction is an ``init`` transaction.
     */
    get to(): null | string;
    set to(value: null | string);
    /**
     *  The transaction nonce.
     */
    get nonce(): number;
    set nonce(value: BigNumberish);
    /**
     *  The gas limit.
     */
    get gasLimit(): bigint;
    set gasLimit(value: BigNumberish);
    /**
     *  The gas price.
     *
     *  On legacy networks this defines the fee that will be paid. On
     *  EIP-1559 networks, this should be ``null``.
     */
    get gasPrice(): null | bigint;
    set gasPrice(value: null | BigNumberish);
    /**
     *  The maximum priority fee per unit of gas to pay. On legacy
     *  networks this should be ``null``.
     */
    get maxPriorityFeePerGas(): null | bigint;
    set maxPriorityFeePerGas(value: null | BigNumberish);
    /**
     *  The maximum total fee per unit of gas to pay. On legacy
     *  networks this should be ``null``.
     */
    get maxFeePerGas(): null | bigint;
    set maxFeePerGas(value: null | BigNumberish);
    /**
     *  The transaction data. For ``init`` transactions this is the
     *  deployment code.
     */
    get data(): string;
    set data(value: BytesLike);
    /**
     *  The amount of ether (in wei) to send in this transactions.
     */
    get value(): bigint;
    set value(value: BigNumberish);
    /**
     *  The chain ID this transaction is valid on.
     */
    get chainId(): bigint;
    set chainId(value: BigNumberish);
    /**
     *  If signed, the signature for this transaction.
     */
    get signature(): null | Signature;
    set signature(value: null | SignatureLike);
    /**
     *  The access list.
     *
     *  An access list permits discounted (but pre-paid) access to
     *  bytecode and state variable access within contract execution.
     */
    get accessList(): null | AccessList;
    set accessList(value: null | AccessListish);
    get authorizationList(): null | Array<Authorization>;
    set authorizationList(auths: null | Array<AuthorizationLike>);
    /**
     *  The max fee per blob gas for Cancun transactions.
     */
    get maxFeePerBlobGas(): null | bigint;
    set maxFeePerBlobGas(value: null | BigNumberish);
    /**
     *  The BLOb versioned hashes for Cancun transactions.
     */
    get blobVersionedHashes(): null | Array<string>;
    set blobVersionedHashes(value: null | Array<string>);
    /**
     *  The BLObs for the Transaction, if any.
     *
     *  If ``blobs`` is non-``null``, then the [[seriailized]]
     *  will return the network formatted sidecar, otherwise it
     *  will return the standard [[link-eip-2718]] payload. The
     *  [[unsignedSerialized]] is unaffected regardless.
     *
     *  When setting ``blobs``, either fully valid [[Blob]] objects
     *  may be specified (i.e. correctly padded, with correct
     *  committments and proofs) or a raw [[BytesLike]] may
     *  be provided.
     *
     *  If raw [[BytesLike]] are provided, the [[kzg]] property **must**
     *  be already set. The blob will be correctly padded and the
     *  [[KzgLibrary]] will be used to compute the committment and
     *  proof for the blob.
     *
     *  A BLOb is a sequence of field elements, each of which must
     *  be within the BLS field modulo, so some additional processing
     *  may be required to encode arbitrary data to ensure each 32 byte
     *  field is within the valid range.
     *
     *  Setting this automatically populates [[blobVersionedHashes]],
     *  overwriting any existing values. Setting this to ``null``
     *  does **not** remove the [[blobVersionedHashes]], leaving them
     *  present.
     */
    get blobs(): null | Array<Blob>;
    set blobs(_blobs: null | Array<BlobLike>);
    get kzg(): null | KzgLibrary;
    set kzg(kzg: null | KzgLibraryLike);
    /**
     *  Creates a new Transaction with default values.
     */
    constructor();
    /**
     *  The transaction hash, if signed. Otherwise, ``null``.
     */
    get hash(): null | string;
    /**
     *  The pre-image hash of this transaction.
     *
     *  This is the digest that a [[Signer]] must sign to authorize
     *  this transaction.
     */
    get unsignedHash(): string;
    /**
     *  The sending address, if signed. Otherwise, ``null``.
     */
    get from(): null | string;
    /**
     *  The public key of the sender, if signed. Otherwise, ``null``.
     */
    get fromPublicKey(): null | string;
    /**
     *  Returns true if signed.
     *
     *  This provides a Type Guard that properties requiring a signed
     *  transaction are non-null.
     */
    isSigned(): this is (Transaction & {
        type: number;
        typeName: string;
        from: string;
        signature: Signature;
    });
    /**
     *  The serialized transaction.
     *
     *  This throws if the transaction is unsigned. For the pre-image,
     *  use [[unsignedSerialized]].
     */
    get serialized(): string;
    /**
     *  The transaction pre-image.
     *
     *  The hash of this is the digest which needs to be signed to
     *  authorize this transaction.
     */
    get unsignedSerialized(): string;
    /**
     *  Return the most "likely" type; currently the highest
     *  supported transaction type.
     */
    inferType(): number;
    /**
     *  Validates the explicit properties and returns a list of compatible
     *  transaction types.
     */
    inferTypes(): Array<number>;
    /**
     *  Returns true if this transaction is a legacy transaction (i.e.
     *  ``type === 0``).
     *
     *  This provides a Type Guard that the related properties are
     *  non-null.
     */
    isLegacy(): this is (Transaction & {
        type: 0;
        gasPrice: bigint;
    });
    /**
     *  Returns true if this transaction is berlin hardform transaction (i.e.
     *  ``type === 1``).
     *
     *  This provides a Type Guard that the related properties are
     *  non-null.
     */
    isBerlin(): this is (Transaction & {
        type: 1;
        gasPrice: bigint;
        accessList: AccessList;
    });
    /**
     *  Returns true if this transaction is london hardform transaction (i.e.
     *  ``type === 2``).
     *
     *  This provides a Type Guard that the related properties are
     *  non-null.
     */
    isLondon(): this is (Transaction & {
        type: 2;
        accessList: AccessList;
        maxFeePerGas: bigint;
        maxPriorityFeePerGas: bigint;
    });
    /**
     *  Returns true if this transaction is an [[link-eip-4844]] BLOB
     *  transaction.
     *
     *  This provides a Type Guard that the related properties are
     *  non-null.
     */
    isCancun(): this is (Transaction & {
        type: 3;
        to: string;
        accessList: AccessList;
        maxFeePerGas: bigint;
        maxPriorityFeePerGas: bigint;
        maxFeePerBlobGas: bigint;
        blobVersionedHashes: Array<string>;
    });
    /**
     *  Create a copy of this transaciton.
     */
    clone(): Transaction;
    /**
     *  Return a JSON-friendly object.
     */
    toJSON(): any;
    /**
     *  Create a **Transaction** from a serialized transaction or a
     *  Transaction-like object.
     */
    static from(tx?: string | TransactionLike<string>): Transaction;
}
//# sourceMappingURL=transaction.d.ts.map