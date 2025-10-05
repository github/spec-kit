import { mod } from './abstract/modular.js';
import { ProjPointType as PointType } from './abstract/weierstrass.js';
import type { Hex, PrivKey } from './abstract/utils.js';
import { bytesToNumberBE, numberToBytesBE } from './abstract/utils.js';
export declare const secp256k1: Readonly<{
    create: (hash: import("./abstract/utils.js").CHash) => import("./abstract/weierstrass.js").CurveFn;
    CURVE: Readonly<{
        readonly nBitLength: number;
        readonly nByteLength: number;
        readonly Fp: import("./abstract/modular.js").IField<bigint>;
        readonly n: bigint;
        readonly h: bigint;
        readonly hEff?: bigint | undefined;
        readonly Gx: bigint;
        readonly Gy: bigint;
        readonly allowInfinityPoint?: boolean | undefined;
        readonly a: bigint;
        readonly b: bigint;
        readonly allowedPrivateKeyLengths?: readonly number[] | undefined;
        readonly wrapPrivateKey?: boolean | undefined;
        readonly endo?: {
            beta: bigint;
            splitScalar: (k: bigint) => {
                k1neg: boolean;
                k1: bigint;
                k2neg: boolean;
                k2: bigint;
            };
        } | undefined;
        readonly isTorsionFree?: ((c: import("./abstract/weierstrass.js").ProjConstructor<bigint>, point: PointType<bigint>) => boolean) | undefined;
        readonly clearCofactor?: ((c: import("./abstract/weierstrass.js").ProjConstructor<bigint>, point: PointType<bigint>) => PointType<bigint>) | undefined;
        readonly hash: import("./abstract/utils.js").CHash;
        readonly hmac: (key: Uint8Array, ...messages: Uint8Array[]) => Uint8Array;
        readonly randomBytes: (bytesLength?: number | undefined) => Uint8Array;
        lowS: boolean;
        readonly bits2int?: ((bytes: Uint8Array) => bigint) | undefined;
        readonly bits2int_modN?: ((bytes: Uint8Array) => bigint) | undefined;
        readonly p: bigint;
    }>;
    getPublicKey: (privateKey: PrivKey, isCompressed?: boolean | undefined) => Uint8Array;
    getSharedSecret: (privateA: PrivKey, publicB: Hex, isCompressed?: boolean | undefined) => Uint8Array;
    sign: (msgHash: Hex, privKey: PrivKey, opts?: import("./abstract/weierstrass.js").SignOpts | undefined) => import("./abstract/weierstrass.js").RecoveredSignatureType;
    verify: (signature: Hex | {
        r: bigint;
        s: bigint;
    }, msgHash: Hex, publicKey: Hex, opts?: import("./abstract/weierstrass.js").VerOpts | undefined) => boolean;
    ProjectivePoint: import("./abstract/weierstrass.js").ProjConstructor<bigint>;
    Signature: import("./abstract/weierstrass.js").SignatureConstructor;
    utils: {
        normPrivateKeyToScalar: (key: PrivKey) => bigint;
        isValidPrivateKey(privateKey: PrivKey): boolean;
        randomPrivateKey: () => Uint8Array;
        precompute: (windowSize?: number | undefined, point?: PointType<bigint> | undefined) => PointType<bigint>;
    };
}>;
declare function taggedHash(tag: string, ...messages: Uint8Array[]): Uint8Array;
/**
 * lift_x from BIP340. Convert 32-byte x coordinate to elliptic curve point.
 * @returns valid point checked for being on-curve
 */
declare function lift_x(x: bigint): PointType<bigint>;
/**
 * Schnorr public key is just `x` coordinate of Point as per BIP340.
 */
declare function schnorrGetPublicKey(privateKey: Hex): Uint8Array;
/**
 * Creates Schnorr signature as per BIP340. Verifies itself before returning anything.
 * auxRand is optional and is not the sole source of k generation: bad CSPRNG won't be dangerous.
 */
declare function schnorrSign(message: Hex, privateKey: PrivKey, auxRand?: Hex): Uint8Array;
/**
 * Verifies Schnorr signature.
 * Will swallow errors & return false except for initial type validation of arguments.
 */
declare function schnorrVerify(signature: Hex, message: Hex, publicKey: Hex): boolean;
export declare const schnorr: {
    getPublicKey: typeof schnorrGetPublicKey;
    sign: typeof schnorrSign;
    verify: typeof schnorrVerify;
    utils: {
        randomPrivateKey: () => Uint8Array;
        lift_x: typeof lift_x;
        pointToBytes: (point: PointType<bigint>) => Uint8Array;
        numberToBytesBE: typeof numberToBytesBE;
        bytesToNumberBE: typeof bytesToNumberBE;
        taggedHash: typeof taggedHash;
        mod: typeof mod;
    };
};
export declare const hashToCurve: (msg: Uint8Array, options?: import("./abstract/hash-to-curve.js").htfBasicOpts | undefined) => import("./abstract/hash-to-curve.js").H2CPoint<bigint>;
export declare const encodeToCurve: (msg: Uint8Array, options?: import("./abstract/hash-to-curve.js").htfBasicOpts | undefined) => import("./abstract/hash-to-curve.js").H2CPoint<bigint>;
export {};
//# sourceMappingURL=secp256k1.d.ts.map