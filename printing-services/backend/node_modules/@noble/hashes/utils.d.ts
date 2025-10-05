/*! noble-hashes - MIT License (c) 2022 Paul Miller (paulmillr.com) */
export type TypedArray = Int8Array | Uint8ClampedArray | Uint8Array | Uint16Array | Int16Array | Uint32Array | Int32Array;
export declare const u8: (arr: TypedArray) => Uint8Array;
export declare const u32: (arr: TypedArray) => Uint32Array;
export declare const createView: (arr: TypedArray) => DataView;
export declare const rotr: (word: number, shift: number) => number;
export declare const isLE: boolean;
/**
 * @example bytesToHex(Uint8Array.from([0xca, 0xfe, 0x01, 0x23])) // 'cafe0123'
 */
export declare function bytesToHex(bytes: Uint8Array): string;
/**
 * @example hexToBytes('cafe0123') // Uint8Array.from([0xca, 0xfe, 0x01, 0x23])
 */
export declare function hexToBytes(hex: string): Uint8Array;
export declare const nextTick: () => Promise<void>;
export declare function asyncLoop(iters: number, tick: number, cb: (i: number) => void): Promise<void>;
/**
 * @example utf8ToBytes('abc') // new Uint8Array([97, 98, 99])
 */
export declare function utf8ToBytes(str: string): Uint8Array;
export type Input = Uint8Array | string;
/**
 * Normalizes (non-hex) string or Uint8Array to Uint8Array.
 * Warning: when Uint8Array is passed, it would NOT get copied.
 * Keep in mind for future mutable operations.
 */
export declare function toBytes(data: Input): Uint8Array;
/**
 * Copies several Uint8Arrays into one.
 */
export declare function concatBytes(...arrays: Uint8Array[]): Uint8Array;
export declare abstract class Hash<T extends Hash<T>> {
    abstract blockLen: number;
    abstract outputLen: number;
    abstract update(buf: Input): this;
    abstract digestInto(buf: Uint8Array): void;
    abstract digest(): Uint8Array;
    /**
     * Resets internal state. Makes Hash instance unusable.
     * Reset is impossible for keyed hashes if key is consumed into state. If digest is not consumed
     * by user, they will need to manually call `destroy()` when zeroing is necessary.
     */
    abstract destroy(): void;
    /**
     * Clones hash instance. Unsafe: doesn't check whether `to` is valid. Can be used as `clone()`
     * when no options are passed.
     * Reasons to use `_cloneInto` instead of clone: 1) performance 2) reuse instance => all internal
     * buffers are overwritten => causes buffer overwrite which is used for digest in some cases.
     * There are no guarantees for clean-up because it's impossible in JS.
     */
    abstract _cloneInto(to?: T): T;
    clone(): T;
}
/**
 * XOF: streaming API to read digest in chunks.
 * Same as 'squeeze' in keccak/k12 and 'seek' in blake3, but more generic name.
 * When hash used in XOF mode it is up to user to call '.destroy' afterwards, since we cannot
 * destroy state, next call can require more bytes.
 */
export type HashXOF<T extends Hash<T>> = Hash<T> & {
    xof(bytes: number): Uint8Array;
    xofInto(buf: Uint8Array): Uint8Array;
};
type EmptyObj = {};
export declare function checkOpts<T1 extends EmptyObj, T2 extends EmptyObj>(defaults: T1, opts?: T2): T1 & T2;
export type CHash = ReturnType<typeof wrapConstructor>;
export declare function wrapConstructor<T extends Hash<T>>(hashCons: () => Hash<T>): {
    (msg: Input): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(): Hash<T>;
};
export declare function wrapConstructorWithOpts<H extends Hash<H>, T extends Object>(hashCons: (opts?: T) => Hash<H>): {
    (msg: Input, opts?: T): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(opts: T): Hash<H>;
};
export declare function wrapXOFConstructorWithOpts<H extends HashXOF<H>, T extends Object>(hashCons: (opts?: T) => HashXOF<H>): {
    (msg: Input, opts?: T): Uint8Array;
    outputLen: number;
    blockLen: number;
    create(opts: T): HashXOF<H>;
};
/**
 * Secure PRNG. Uses `crypto.getRandomValues`, which defers to OS.
 */
export declare function randomBytes(bytesLength?: number): Uint8Array;
export {};
