/*! noble-curves - MIT License (c) 2022 Paul Miller (paulmillr.com) */
import type { Group, GroupConstructor, AffinePoint } from './curve.js';
import { IField } from './modular.js';
import { CHash } from './utils.js';
/**
 * * `DST` is a domain separation tag, defined in section 2.2.5
 * * `p` characteristic of F, where F is a finite field of characteristic p and order q = p^m
 * * `m` is extension degree (1 for prime fields)
 * * `k` is the target security target in bits (e.g. 128), from section 5.1
 * * `expand` is `xmd` (SHA2, SHA3, BLAKE) or `xof` (SHAKE, BLAKE-XOF)
 * * `hash` conforming to `utils.CHash` interface, with `outputLen` / `blockLen` props
 */
type UnicodeOrBytes = string | Uint8Array;
export type Opts = {
    DST: UnicodeOrBytes;
    p: bigint;
    m: number;
    k: number;
    expand: 'xmd' | 'xof';
    hash: CHash;
};
export declare function expand_message_xmd(msg: Uint8Array, DST: Uint8Array, lenInBytes: number, H: CHash): Uint8Array;
export declare function expand_message_xof(msg: Uint8Array, DST: Uint8Array, lenInBytes: number, k: number, H: CHash): Uint8Array;
/**
 * Hashes arbitrary-length byte strings to a list of one or more elements of a finite field F
 * https://www.rfc-editor.org/rfc/rfc9380#section-5.2
 * @param msg a byte string containing the message to hash
 * @param count the number of elements of F to output
 * @param options `{DST: string, p: bigint, m: number, k: number, expand: 'xmd' | 'xof', hash: H}`, see above
 * @returns [u_0, ..., u_(count - 1)], a list of field elements.
 */
export declare function hash_to_field(msg: Uint8Array, count: number, options: Opts): bigint[][];
export declare function isogenyMap<T, F extends IField<T>>(field: F, map: [T[], T[], T[], T[]]): (x: T, y: T) => {
    x: T;
    y: T;
};
export interface H2CPoint<T> extends Group<H2CPoint<T>> {
    add(rhs: H2CPoint<T>): H2CPoint<T>;
    toAffine(iz?: bigint): AffinePoint<T>;
    clearCofactor(): H2CPoint<T>;
    assertValidity(): void;
}
export interface H2CPointConstructor<T> extends GroupConstructor<H2CPoint<T>> {
    fromAffine(ap: AffinePoint<T>): H2CPoint<T>;
}
export type MapToCurve<T> = (scalar: bigint[]) => AffinePoint<T>;
export type htfBasicOpts = {
    DST: UnicodeOrBytes;
};
export declare function createHasher<T>(Point: H2CPointConstructor<T>, mapToCurve: MapToCurve<T>, def: Opts & {
    encodeDST?: UnicodeOrBytes;
}): {
    hashToCurve(msg: Uint8Array, options?: htfBasicOpts): H2CPoint<T>;
    encodeToCurve(msg: Uint8Array, options?: htfBasicOpts): H2CPoint<T>;
};
export {};
//# sourceMappingURL=hash-to-curve.d.ts.map