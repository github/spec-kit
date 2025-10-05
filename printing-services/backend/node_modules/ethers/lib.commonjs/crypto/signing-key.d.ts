/**
 *  Add details about signing here.
 *
 *  @_subsection: api/crypto:Signing  [about-signing]
 */
import { Signature } from "./signature.js";
import type { BytesLike } from "../utils/index.js";
import type { SignatureLike } from "./index.js";
/**
 *  A **SigningKey** provides high-level access to the elliptic curve
 *  cryptography (ECC) operations and key management.
 */
export declare class SigningKey {
    #private;
    /**
     *  Creates a new **SigningKey** for %%privateKey%%.
     */
    constructor(privateKey: BytesLike);
    /**
     *  The private key.
     */
    get privateKey(): string;
    /**
     *  The uncompressed public key.
     *
     * This will always begin with the prefix ``0x04`` and be 132
     * characters long (the ``0x`` prefix and 130 hexadecimal nibbles).
     */
    get publicKey(): string;
    /**
     *  The compressed public key.
     *
     *  This will always begin with either the prefix ``0x02`` or ``0x03``
     *  and be 68 characters long (the ``0x`` prefix and 33 hexadecimal
     *  nibbles)
     */
    get compressedPublicKey(): string;
    /**
     *  Return the signature of the signed %%digest%%.
     */
    sign(digest: BytesLike): Signature;
    /**
     *  Returns the [[link-wiki-ecdh]] shared secret between this
     *  private key and the %%other%% key.
     *
     *  The %%other%% key may be any type of key, a raw public key,
     *  a compressed/uncompressed pubic key or aprivate key.
     *
     *  Best practice is usually to use a cryptographic hash on the
     *  returned value before using it as a symetric secret.
     *
     *  @example:
     *    sign1 = new SigningKey(id("some-secret-1"))
     *    sign2 = new SigningKey(id("some-secret-2"))
     *
     *    // Notice that privA.computeSharedSecret(pubB)...
     *    sign1.computeSharedSecret(sign2.publicKey)
     *    //_result:
     *
     *    // ...is equal to privB.computeSharedSecret(pubA).
     *    sign2.computeSharedSecret(sign1.publicKey)
     *    //_result:
     */
    computeSharedSecret(other: BytesLike): string;
    /**
     *  Compute the public key for %%key%%, optionally %%compressed%%.
     *
     *  The %%key%% may be any type of key, a raw public key, a
     *  compressed/uncompressed public key or private key.
     *
     *  @example:
     *    sign = new SigningKey(id("some-secret"));
     *
     *    // Compute the uncompressed public key for a private key
     *    SigningKey.computePublicKey(sign.privateKey)
     *    //_result:
     *
     *    // Compute the compressed public key for a private key
     *    SigningKey.computePublicKey(sign.privateKey, true)
     *    //_result:
     *
     *    // Compute the uncompressed public key
     *    SigningKey.computePublicKey(sign.publicKey, false);
     *    //_result:
     *
     *    // Compute the Compressed a public key
     *    SigningKey.computePublicKey(sign.publicKey, true);
     *    //_result:
     */
    static computePublicKey(key: BytesLike, compressed?: boolean): string;
    /**
     *  Returns the public key for the private key which produced the
     *  %%signature%% for the given %%digest%%.
     *
     *  @example:
     *    key = new SigningKey(id("some-secret"))
     *    digest = id("hello world")
     *    sig = key.sign(digest)
     *
     *    // Notice the signer public key...
     *    key.publicKey
     *    //_result:
     *
     *    // ...is equal to the recovered public key
     *    SigningKey.recoverPublicKey(digest, sig)
     *    //_result:
     *
     */
    static recoverPublicKey(digest: BytesLike, signature: SignatureLike): string;
    /**
     *  Returns the point resulting from adding the ellipic curve points
     *  %%p0%% and %%p1%%.
     *
     *  This is not a common function most developers should require, but
     *  can be useful for certain privacy-specific techniques.
     *
     *  For example, it is used by [[HDNodeWallet]] to compute child
     *  addresses from parent public keys and chain codes.
     */
    static addPoints(p0: BytesLike, p1: BytesLike, compressed?: boolean): string;
}
//# sourceMappingURL=signing-key.d.ts.map