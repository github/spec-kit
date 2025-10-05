import { ExtPointType } from './abstract/edwards.js';
import { htfBasicOpts } from './abstract/hash-to-curve.js';
import { Hex } from './abstract/utils.js';
import { AffinePoint } from './abstract/curve.js';
export declare const ed448: import("./abstract/edwards.js").CurveFn;
export declare const ed448ph: import("./abstract/edwards.js").CurveFn;
export declare const x448: import("./abstract/montgomery.js").CurveFn;
/**
 * Converts edwards448 public key to x448 public key. Uses formula:
 * * `(u, v) = ((y-1)/(y+1), sqrt(156324)*u/x)`
 * * `(x, y) = (sqrt(156324)*u/v, (1+u)/(1-u))`
 * @example
 *   const aPub = ed448.getPublicKey(utils.randomPrivateKey());
 *   x448.getSharedSecret(edwardsToMontgomery(aPub), edwardsToMontgomery(someonesPub))
 */
export declare function edwardsToMontgomeryPub(edwardsPub: string | Uint8Array): Uint8Array;
export declare const edwardsToMontgomery: typeof edwardsToMontgomeryPub;
export declare const hashToCurve: (msg: Uint8Array, options?: htfBasicOpts | undefined) => import("./abstract/hash-to-curve.js").H2CPoint<bigint>;
export declare const encodeToCurve: (msg: Uint8Array, options?: htfBasicOpts | undefined) => import("./abstract/hash-to-curve.js").H2CPoint<bigint>;
type ExtendedPoint = ExtPointType;
/**
 * Each ed448/ExtendedPoint has 4 different equivalent points. This can be
 * a source of bugs for protocols like ring signatures. Decaf was created to solve this.
 * Decaf point operates in X:Y:Z:T extended coordinates like ExtendedPoint,
 * but it should work in its own namespace: do not combine those two.
 * https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-ristretto255-decaf448
 */
declare class DcfPoint {
    private readonly ep;
    static BASE: DcfPoint;
    static ZERO: DcfPoint;
    constructor(ep: ExtendedPoint);
    static fromAffine(ap: AffinePoint<bigint>): DcfPoint;
    /**
     * Takes uniform output of 112-byte hash function like shake256 and converts it to `DecafPoint`.
     * The hash-to-group operation applies Elligator twice and adds the results.
     * **Note:** this is one-way map, there is no conversion from point to hash.
     * https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-ristretto255-decaf448-07#name-element-derivation-2
     * @param hex 112-byte output of a hash function
     */
    static hashToCurve(hex: Hex): DcfPoint;
    /**
     * Converts decaf-encoded string to decaf point.
     * https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-ristretto255-decaf448-07#name-decode-2
     * @param hex Decaf-encoded 56 bytes. Not every 56-byte string is valid decaf encoding
     */
    static fromHex(hex: Hex): DcfPoint;
    /**
     * Encodes decaf point to Uint8Array.
     * https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-ristretto255-decaf448-07#name-encode-2
     */
    toRawBytes(): Uint8Array;
    toHex(): string;
    toString(): string;
    equals(other: DcfPoint): boolean;
    add(other: DcfPoint): DcfPoint;
    subtract(other: DcfPoint): DcfPoint;
    multiply(scalar: bigint): DcfPoint;
    multiplyUnsafe(scalar: bigint): DcfPoint;
}
export declare const DecafPoint: typeof DcfPoint;
export declare const hashToDecaf448: (msg: Uint8Array, options: htfBasicOpts) => DcfPoint;
export declare const hash_to_decaf448: (msg: Uint8Array, options: htfBasicOpts) => DcfPoint;
export {};
//# sourceMappingURL=ed448.d.ts.map