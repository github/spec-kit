/**
 * jubjub Twisted Edwards curve.
 * https://neuromancer.sk/std/other/JubJub
 * jubjub does not use EdDSA, so `hash`/sha512 params are passed because interface expects them.
 */
export declare const jubjub: import("./abstract/edwards.js").CurveFn;
export declare function groupHash(tag: Uint8Array, personalization: Uint8Array): import("./abstract/edwards.js").ExtPointType;
export declare function findGroupHash(m: Uint8Array, personalization: Uint8Array): import("./abstract/edwards.js").ExtPointType;
//# sourceMappingURL=jubjub.d.ts.map