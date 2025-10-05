import { BLAKE2, BlakeOpts } from './_blake2.js';
export declare const IV: Uint32Array;
export declare function compress(s: Uint8Array, offset: number, msg: Uint32Array, rounds: number, v0: number, v1: number, v2: number, v3: number, v4: number, v5: number, v6: number, v7: number, v8: number, v9: number, v10: number, v11: number, v12: number, v13: number, v14: number, v15: number): {
    v0: number;
    v1: number;
    v2: number;
    v3: number;
    v4: number;
    v5: number;
    v6: number;
    v7: number;
    v8: number;
    v9: number;
    v10: number;
    v11: number;
    v12: number;
    v13: number;
    v14: number;
    v15: number;
};
declare class BLAKE2s extends BLAKE2<BLAKE2s> {
    private v0;
    private v1;
    private v2;
    private v3;
    private v4;
    private v5;
    private v6;
    private v7;
    constructor(opts?: BlakeOpts);
    protected get(): [number, number, number, number, number, number, number, number];
    protected set(v0: number, v1: number, v2: number, v3: number, v4: number, v5: number, v6: number, v7: number): void;
    protected compress(msg: Uint32Array, offset: number, isLast: boolean): void;
    destroy(): void;
}
/**
 * BLAKE2s - optimized for 32-bit platforms. JS doesn't have uint64, so it's faster than BLAKE2b.
 * @param msg - message that would be hashed
 * @param opts - dkLen, key, salt, personalization
 */
export declare const blake2s: {
    (msg: import("./utils.js").Input, opts?: BlakeOpts | undefined): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(opts: BlakeOpts): import("./utils.js").Hash<BLAKE2s>;
};
export {};
