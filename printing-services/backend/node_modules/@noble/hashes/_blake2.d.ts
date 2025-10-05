import { Hash, Input } from './utils.js';
export declare const SIGMA: Uint8Array;
export type BlakeOpts = {
    dkLen?: number;
    key?: Input;
    salt?: Input;
    personalization?: Input;
};
export declare abstract class BLAKE2<T extends BLAKE2<T>> extends Hash<T> {
    readonly blockLen: number;
    outputLen: number;
    protected abstract compress(msg: Uint32Array, offset: number, isLast: boolean): void;
    protected abstract get(): number[];
    protected abstract set(...args: number[]): void;
    abstract destroy(): void;
    protected buffer: Uint8Array;
    protected buffer32: Uint32Array;
    protected length: number;
    protected pos: number;
    protected finished: boolean;
    protected destroyed: boolean;
    constructor(blockLen: number, outputLen: number, opts: BlakeOpts | undefined, keyLen: number, saltLen: number, persLen: number);
    update(data: Input): this;
    digestInto(out: Uint8Array): void;
    digest(): Uint8Array;
    _cloneInto(to?: T): T;
}
