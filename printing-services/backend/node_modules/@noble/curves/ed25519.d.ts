import { ExtPointType } from './abstract/edwards.js';
import { Hex } from './abstract/utils.js';
import { htfBasicOpts } from './abstract/hash-to-curve.js';
import { AffinePoint } from './abstract/curve.js';
export declare const ED25519_TORSION_SUBGROUP: string[];
export declare const ed25519: import("./abstract/edwards.js").CurveFn;
export declare const ed25519ctx: import("./abstract/edwards.js").CurveFn;
export declare const ed25519ph: import("./abstract/edwards.js").CurveFn;
export declare const x25519: import("./abstract/montgomery.js").CurveFn;
/**
 * Converts ed25519 public key to x25519 public key. Uses formula:
 * * `(u, v) = ((1+y)/(1-y), sqrt(-486664)*u/x)`
 * * `(x, y) = (sqrt(-486664)*u/v, (u-1)/(u+1))`
 * @example
 *   const someonesPub = ed25519.getPublicKey(ed25519.utils.randomPrivateKey());
 *   const aPriv = x25519.utils.randomPrivateKey();
 *   x25519.getSharedSecret(aPriv, edwardsToMontgomeryPub(someonesPub))
 */
export declare function edwardsToMontgomeryPub(edwardsPub: Hex): Uint8Array;
export declare const edwardsToMontgomery: typeof edwardsToMontgomeryPub;
/**
 * Converts ed25519 secret key to x25519 secret key.
 * @example
 *   const someonesPub = x25519.getPublicKey(x25519.utils.randomPrivateKey());
 *   const aPriv = ed25519.utils.randomPrivateKey();
 *   x25519.getSharedSecret(edwardsToMontgomeryPriv(aPriv), someonesPub)
 */
export declare function edwardsToMontgomeryPriv(edwardsPriv: Uint8Array): Uint8Array;
export declare const hashToCurve: (msg: Uint8Array, options?: htfBasicOpts | undefined) => import("./abstract/hash-to-curve.js").H2CPoint<bigint>;
export declare const encodeToCurve: (msg: Uint8Array, options?: htfBasicOpts | undefined) => import("./abstract/hash-to-curve.js").H2CPoint<bigint>;
type ExtendedPoint = ExtPointType;
/**
 * Each ed25519/ExtendedPoint has 8 different equivalent points. This can be
 * a source of bugs for protocols like ring signatures. Ristretto was created to solve this.
 * Ristretto point operates in X:Y:Z:T extended coordinates like ExtendedPoint,
 * but it should work in its own namespace: do not combine those two.
 * https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-ristretto255-decaf448
 */
declare class RistPoint {
    private readonly ep;
    static BASE: RistPoint;
    static ZERO: RistPoint;
    constructor(ep: ExtendedPoint);
    static fromAffine(ap: AffinePoint<bigint>): RistPoint;
    /**
     * Takes uniform output of 64-byte hash function like sha512 and converts it to `RistrettoPoint`.
     * The hash-to-group operation applies Elligator twice and adds the results.
     * **Note:** this is one-way map, there is no conversion from point to hash.
     * https://ristretto.group/formulas/elligator.html
     * @param hex 64-byte output of a hash function
     */
    static hashToCurve(hex: Hex): RistPoint;
    /**
     * Converts ristretto-encoded string to ristretto point.
     * https://ristretto.group/formulas/decoding.html
     * @param hex Ristretto-encoded 32 bytes. Not every 32-byte string is valid ristretto encoding
     */
    static fromHex(hex: Hex): RistPoint;
    /**
     * Encodes ristretto point to Uint8Array.
     * https://ristretto.group/formulas/encoding.html
     */
    toRawBytes(): Uint8Array;
    toHex(): string;
    toString(): string;
    equals(other: RistPoint): boolean;
    add(other: RistPoint): RistPoint;
    subtract(other: RistPoint): RistPoint;
    multiply(scalar: bigint): RistPoint;
    multiplyUnsafe(scalar: bigint): RistPoint;
}
export declare const RistrettoPoint: typeof RistPoint;
export declare const hashToRistretto255: (msg: Uint8Array, options: htfBasicOpts) => RistPoint;
export declare const hash_to_ristretto255: (msg: Uint8Array, options: htfBasicOpts) => RistPoint;
export {};
//# sourceMappingURL=ed25519.d.ts.map