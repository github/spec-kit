type Hex = string | Uint8Array;
export type CurveType = {
    P: bigint;
    nByteLength: number;
    adjustScalarBytes?: (bytes: Uint8Array) => Uint8Array;
    domain?: (data: Uint8Array, ctx: Uint8Array, phflag: boolean) => Uint8Array;
    a: bigint;
    montgomeryBits: number;
    powPminus2?: (x: bigint) => bigint;
    xyToU?: (x: bigint, y: bigint) => bigint;
    Gu: bigint;
    randomBytes?: (bytesLength?: number) => Uint8Array;
};
export type CurveFn = {
    scalarMult: (scalar: Hex, u: Hex) => Uint8Array;
    scalarMultBase: (scalar: Hex) => Uint8Array;
    getSharedSecret: (privateKeyA: Hex, publicKeyB: Hex) => Uint8Array;
    getPublicKey: (privateKey: Hex) => Uint8Array;
    utils: {
        randomPrivateKey: () => Uint8Array;
    };
    GuBytes: Uint8Array;
};
export declare function montgomery(curveDef: CurveType): CurveFn;
export {};
//# sourceMappingURL=montgomery.d.ts.map