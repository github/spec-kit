import { Hash, Input, HashXOF } from './utils.js';
export declare function keccakP(s: Uint32Array, rounds?: number): void;
export declare class Keccak extends Hash<Keccak> implements HashXOF<Keccak> {
    blockLen: number;
    suffix: number;
    outputLen: number;
    protected enableXOF: boolean;
    protected rounds: number;
    protected state: Uint8Array;
    protected pos: number;
    protected posOut: number;
    protected finished: boolean;
    protected state32: Uint32Array;
    protected destroyed: boolean;
    constructor(blockLen: number, suffix: number, outputLen: number, enableXOF?: boolean, rounds?: number);
    protected keccak(): void;
    update(data: Input): this;
    protected finish(): void;
    protected writeInto(out: Uint8Array): Uint8Array;
    xofInto(out: Uint8Array): Uint8Array;
    xof(bytes: number): Uint8Array;
    digestInto(out: Uint8Array): Uint8Array;
    digest(): Uint8Array;
    destroy(): void;
    _cloneInto(to?: Keccak): Keccak;
}
export declare const sha3_224: {
    (msg: Input): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(): Hash<Keccak>;
};
/**
 * SHA3-256 hash function
 * @param message - that would be hashed
 */
export declare const sha3_256: {
    (msg: Input): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(): Hash<Keccak>;
};
export declare const sha3_384: {
    (msg: Input): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(): Hash<Keccak>;
};
export declare const sha3_512: {
    (msg: Input): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(): Hash<Keccak>;
};
export declare const keccak_224: {
    (msg: Input): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(): Hash<Keccak>;
};
/**
 * keccak-256 hash function. Different from SHA3-256.
 * @param message - that would be hashed
 */
export declare const keccak_256: {
    (msg: Input): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(): Hash<Keccak>;
};
export declare const keccak_384: {
    (msg: Input): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(): Hash<Keccak>;
};
export declare const keccak_512: {
    (msg: Input): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(): Hash<Keccak>;
};
export type ShakeOpts = {
    dkLen?: number;
};
export declare const shake128: {
    (msg: Input, opts?: ShakeOpts | undefined): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(opts: ShakeOpts): HashXOF<HashXOF<Keccak>>;
};
export declare const shake256: {
    (msg: Input, opts?: ShakeOpts | undefined): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(opts: ShakeOpts): HashXOF<HashXOF<Keccak>>;
};
