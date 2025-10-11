import { SHA2 } from './_sha2.js';
export declare class RIPEMD160 extends SHA2<RIPEMD160> {
    private h0;
    private h1;
    private h2;
    private h3;
    private h4;
    constructor();
    protected get(): [number, number, number, number, number];
    protected set(h0: number, h1: number, h2: number, h3: number, h4: number): void;
    protected process(view: DataView, offset: number): void;
    protected roundClean(): void;
    destroy(): void;
}
/**
 * RIPEMD-160 - a hash function from 1990s.
 * @param message - msg that would be hashed
 */
export declare const ripemd160: {
    (msg: import("./utils.js").Input): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(): import("./utils.js").Hash<RIPEMD160>;
};
