import { Input, Hash, HashXOF } from './utils.js';
import { Keccak, ShakeOpts } from './sha3.js';
export type cShakeOpts = ShakeOpts & {
    personalization?: Input;
    NISTfn?: Input;
};
export declare const cshake128: {
    (msg: Input, opts?: cShakeOpts | undefined): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(opts: cShakeOpts): Hash<Keccak>;
};
export declare const cshake256: {
    (msg: Input, opts?: cShakeOpts | undefined): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(opts: cShakeOpts): Hash<Keccak>;
};
declare class KMAC extends Keccak implements HashXOF<KMAC> {
    constructor(blockLen: number, outputLen: number, enableXOF: boolean, key: Input, opts?: cShakeOpts);
    protected finish(): void;
    _cloneInto(to?: KMAC): KMAC;
    clone(): KMAC;
}
export declare const kmac128: {
    (key: Input, message: Input, opts?: cShakeOpts): Uint8Array;
    create(key: Input, opts?: cShakeOpts): KMAC;
};
export declare const kmac256: {
    (key: Input, message: Input, opts?: cShakeOpts): Uint8Array;
    create(key: Input, opts?: cShakeOpts): KMAC;
};
export declare const kmac128xof: {
    (key: Input, message: Input, opts?: cShakeOpts): Uint8Array;
    create(key: Input, opts?: cShakeOpts): KMAC;
};
export declare const kmac256xof: {
    (key: Input, message: Input, opts?: cShakeOpts): Uint8Array;
    create(key: Input, opts?: cShakeOpts): KMAC;
};
declare class TupleHash extends Keccak implements HashXOF<TupleHash> {
    constructor(blockLen: number, outputLen: number, enableXOF: boolean, opts?: cShakeOpts);
    protected finish(): void;
    _cloneInto(to?: TupleHash): TupleHash;
    clone(): TupleHash;
}
export declare const tuplehash128: {
    (messages: Input[], opts?: cShakeOpts): Uint8Array;
    create(opts?: cShakeOpts): TupleHash;
};
export declare const tuplehash256: {
    (messages: Input[], opts?: cShakeOpts): Uint8Array;
    create(opts?: cShakeOpts): TupleHash;
};
export declare const tuplehash128xof: {
    (messages: Input[], opts?: cShakeOpts): Uint8Array;
    create(opts?: cShakeOpts): TupleHash;
};
export declare const tuplehash256xof: {
    (messages: Input[], opts?: cShakeOpts): Uint8Array;
    create(opts?: cShakeOpts): TupleHash;
};
type ParallelOpts = cShakeOpts & {
    blockLen?: number;
};
declare class ParallelHash extends Keccak implements HashXOF<ParallelHash> {
    protected leafCons: () => Hash<Keccak>;
    private leafHash?;
    private chunkPos;
    private chunksDone;
    private chunkLen;
    constructor(blockLen: number, outputLen: number, leafCons: () => Hash<Keccak>, enableXOF: boolean, opts?: ParallelOpts);
    protected finish(): void;
    _cloneInto(to?: ParallelHash): ParallelHash;
    destroy(): void;
    clone(): ParallelHash;
}
export declare const parallelhash128: {
    (message: Input, opts?: ParallelOpts): Uint8Array;
    create(opts?: ParallelOpts): ParallelHash;
};
export declare const parallelhash256: {
    (message: Input, opts?: ParallelOpts): Uint8Array;
    create(opts?: ParallelOpts): ParallelHash;
};
export declare const parallelhash128xof: {
    (message: Input, opts?: ParallelOpts): Uint8Array;
    create(opts?: ParallelOpts): ParallelHash;
};
export declare const parallelhash256xof: {
    (message: Input, opts?: ParallelOpts): Uint8Array;
    create(opts?: ParallelOpts): ParallelHash;
};
export type KangarooOpts = {
    dkLen?: number;
    personalization?: Input;
};
declare class KangarooTwelve extends Keccak implements HashXOF<KangarooTwelve> {
    protected leafLen: number;
    readonly chunkLen = 8192;
    private leafHash?;
    private personalization;
    private chunkPos;
    private chunksDone;
    constructor(blockLen: number, leafLen: number, outputLen: number, rounds: number, opts: KangarooOpts);
    update(data: Input): this;
    protected finish(): void;
    destroy(): void;
    _cloneInto(to?: KangarooTwelve): KangarooTwelve;
    clone(): KangarooTwelve;
}
export declare const k12: {
    (msg: Input, opts?: KangarooOpts | undefined): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(opts: KangarooOpts): Hash<KangarooTwelve>;
};
export declare const m14: {
    (msg: Input, opts?: KangarooOpts | undefined): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(opts: KangarooOpts): Hash<KangarooTwelve>;
};
declare class KeccakPRG extends Keccak {
    protected rate: number;
    constructor(capacity: number);
    keccak(): void;
    update(data: Input): this;
    feed(data: Input): this;
    protected finish(): void;
    digestInto(_out: Uint8Array): Uint8Array;
    fetch(bytes: number): Uint8Array;
    forget(): void;
    _cloneInto(to?: KeccakPRG): KeccakPRG;
    clone(): KeccakPRG;
}
export declare const keccakprg: (capacity?: number) => KeccakPRG;
export {};
