import { BLAKE2 } from './_blake2.js';
import { Input, HashXOF } from './utils.js';
export type Blake3Opts = {
    dkLen?: number;
    key?: Input;
    context?: Input;
};
declare class BLAKE3 extends BLAKE2<BLAKE3> implements HashXOF<BLAKE3> {
    private IV;
    private flags;
    private state;
    private chunkPos;
    private chunksDone;
    private stack;
    private posOut;
    private bufferOut32;
    private bufferOut;
    private chunkOut;
    private enableXOF;
    constructor(opts?: Blake3Opts, flags?: number);
    protected get(): never[];
    protected set(): void;
    private b2Compress;
    protected compress(buf: Uint32Array, bufPos?: number, isLast?: boolean): void;
    _cloneInto(to?: BLAKE3): BLAKE3;
    destroy(): void;
    private b2CompressOut;
    protected finish(): void;
    private writeInto;
    xofInto(out: Uint8Array): Uint8Array;
    xof(bytes: number): Uint8Array;
    digestInto(out: Uint8Array): Uint8Array;
    digest(): Uint8Array;
}
/**
 * BLAKE3 hash function.
 * @param msg - message that would be hashed
 * @param opts - dkLen, key, context
 */
export declare const blake3: {
    (msg: Input, opts?: Blake3Opts | undefined): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(opts: Blake3Opts): HashXOF<BLAKE3>;
};
export {};
