import { randomBytes } from '@noble/hashes/utils';
import { CurveType } from './abstract/weierstrass.js';
import { CHash } from './abstract/utils.js';
export declare function getHash(hash: CHash): {
    hash: CHash;
    hmac: (key: Uint8Array, ...msgs: Uint8Array[]) => Uint8Array;
    randomBytes: typeof randomBytes;
};
type CurveDef = Readonly<Omit<CurveType, 'hash' | 'hmac' | 'randomBytes'>>;
export declare function createCurve(curveDef: CurveDef, defHash: CHash): Readonly<{
    create: (hash: CHash) => import("./abstract/weierstrass.js").CurveFn;
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
        readonly isTorsionFree?: ((c: import("./abstract/weierstrass.js").ProjConstructor<bigint>, point: import("./abstract/weierstrass.js").ProjPointType<bigint>) => boolean) | undefined;
        readonly clearCofactor?: ((c: import("./abstract/weierstrass.js").ProjConstructor<bigint>, point: import("./abstract/weierstrass.js").ProjPointType<bigint>) => import("./abstract/weierstrass.js").ProjPointType<bigint>) | undefined;
        readonly hash: CHash;
        readonly hmac: (key: Uint8Array, ...messages: Uint8Array[]) => Uint8Array;
        readonly randomBytes: (bytesLength?: number | undefined) => Uint8Array;
        lowS: boolean;
        readonly bits2int?: ((bytes: Uint8Array) => bigint) | undefined;
        readonly bits2int_modN?: ((bytes: Uint8Array) => bigint) | undefined;
        readonly p: bigint;
    }>;
    getPublicKey: (privateKey: import("./abstract/utils.js").PrivKey, isCompressed?: boolean | undefined) => Uint8Array;
    getSharedSecret: (privateA: import("./abstract/utils.js").PrivKey, publicB: import("./abstract/utils.js").Hex, isCompressed?: boolean | undefined) => Uint8Array;
    sign: (msgHash: import("./abstract/utils.js").Hex, privKey: import("./abstract/utils.js").PrivKey, opts?: import("./abstract/weierstrass.js").SignOpts | undefined) => import("./abstract/weierstrass.js").RecoveredSignatureType;
    verify: (signature: import("./abstract/utils.js").Hex | {
        r: bigint;
        s: bigint;
    }, msgHash: import("./abstract/utils.js").Hex, publicKey: import("./abstract/utils.js").Hex, opts?: import("./abstract/weierstrass.js").VerOpts | undefined) => boolean;
    ProjectivePoint: import("./abstract/weierstrass.js").ProjConstructor<bigint>;
    Signature: import("./abstract/weierstrass.js").SignatureConstructor;
    utils: {
        normPrivateKeyToScalar: (key: import("./abstract/utils.js").PrivKey) => bigint;
        isValidPrivateKey(privateKey: import("./abstract/utils.js").PrivKey): boolean;
        randomPrivateKey: () => Uint8Array;
        precompute: (windowSize?: number | undefined, point?: import("./abstract/weierstrass.js").ProjPointType<bigint> | undefined) => import("./abstract/weierstrass.js").ProjPointType<bigint>;
    };
}>;
export {};
//# sourceMappingURL=_shortw_utils.d.ts.map