import * as ut from './utils.js';
import { FHash, Hex } from './utils.js';
import { Group, GroupConstructor, BasicCurve, AffinePoint } from './curve.js';
export type CurveType = BasicCurve<bigint> & {
    a: bigint;
    d: bigint;
    hash: FHash;
    randomBytes: (bytesLength?: number) => Uint8Array;
    adjustScalarBytes?: (bytes: Uint8Array) => Uint8Array;
    domain?: (data: Uint8Array, ctx: Uint8Array, phflag: boolean) => Uint8Array;
    uvRatio?: (u: bigint, v: bigint) => {
        isValid: boolean;
        value: bigint;
    };
    prehash?: FHash;
    mapToCurve?: (scalar: bigint[]) => AffinePoint<bigint>;
};
declare function validateOpts(curve: CurveType): Readonly<{
    readonly nBitLength: number;
    readonly nByteLength: number;
    readonly Fp: import("./modular.js").IField<bigint>;
    readonly n: bigint;
    readonly h: bigint;
    readonly hEff?: bigint | undefined;
    readonly Gx: bigint;
    readonly Gy: bigint;
    readonly allowInfinityPoint?: boolean | undefined;
    readonly a: bigint;
    readonly d: bigint;
    readonly hash: ut.FHash;
    readonly randomBytes: (bytesLength?: number | undefined) => Uint8Array;
    readonly adjustScalarBytes?: ((bytes: Uint8Array) => Uint8Array) | undefined;
    readonly domain?: ((data: Uint8Array, ctx: Uint8Array, phflag: boolean) => Uint8Array) | undefined;
    readonly uvRatio?: ((u: bigint, v: bigint) => {
        isValid: boolean;
        value: bigint;
    }) | undefined;
    readonly prehash?: ut.FHash | undefined;
    readonly mapToCurve?: ((scalar: bigint[]) => AffinePoint<bigint>) | undefined;
    readonly p: bigint;
}>;
export interface ExtPointType extends Group<ExtPointType> {
    readonly ex: bigint;
    readonly ey: bigint;
    readonly ez: bigint;
    readonly et: bigint;
    get x(): bigint;
    get y(): bigint;
    assertValidity(): void;
    multiply(scalar: bigint): ExtPointType;
    multiplyUnsafe(scalar: bigint): ExtPointType;
    isSmallOrder(): boolean;
    isTorsionFree(): boolean;
    clearCofactor(): ExtPointType;
    toAffine(iz?: bigint): AffinePoint<bigint>;
    toRawBytes(isCompressed?: boolean): Uint8Array;
    toHex(isCompressed?: boolean): string;
}
export interface ExtPointConstructor extends GroupConstructor<ExtPointType> {
    new (x: bigint, y: bigint, z: bigint, t: bigint): ExtPointType;
    fromAffine(p: AffinePoint<bigint>): ExtPointType;
    fromHex(hex: Hex): ExtPointType;
    fromPrivateKey(privateKey: Hex): ExtPointType;
}
export type CurveFn = {
    CURVE: ReturnType<typeof validateOpts>;
    getPublicKey: (privateKey: Hex) => Uint8Array;
    sign: (message: Hex, privateKey: Hex, options?: {
        context?: Hex;
    }) => Uint8Array;
    verify: (sig: Hex, message: Hex, publicKey: Hex, options?: {
        context?: Hex;
        zip215: boolean;
    }) => boolean;
    ExtendedPoint: ExtPointConstructor;
    utils: {
        randomPrivateKey: () => Uint8Array;
        getExtendedPublicKey: (key: Hex) => {
            head: Uint8Array;
            prefix: Uint8Array;
            scalar: bigint;
            point: ExtPointType;
            pointBytes: Uint8Array;
        };
    };
};
export declare function twistedEdwards(curveDef: CurveType): CurveFn;
export {};
//# sourceMappingURL=edwards.d.ts.map