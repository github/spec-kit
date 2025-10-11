export type Hex = Uint8Array | string;
export type PrivKey = Hex | bigint;
export type CHash = {
    (message: Uint8Array | string): Uint8Array;
    blockLen: number;
    outputLen: number;
    create(opts?: {
        dkLen?: number;
    }): any;
};
export type FHash = (message: Uint8Array | string) => Uint8Array;
/**
 * @example bytesToHex(Uint8Array.from([0xca, 0xfe, 0x01, 0x23])) // 'cafe0123'
 */
export declare function bytesToHex(bytes: Uint8Array): string;
export declare function numberToHexUnpadded(num: number | bigint): string;
export declare function hexToNumber(hex: string): bigint;
/**
 * @example hexToBytes('cafe0123') // Uint8Array.from([0xca, 0xfe, 0x01, 0x23])
 */
export declare function hexToBytes(hex: string): Uint8Array;
export declare function bytesToNumberBE(bytes: Uint8Array): bigint;
export declare function bytesToNumberLE(bytes: Uint8Array): bigint;
export declare function numberToBytesBE(n: number | bigint, len: number): Uint8Array;
export declare function numberToBytesLE(n: number | bigint, len: number): Uint8Array;
export declare function numberToVarBytesBE(n: number | bigint): Uint8Array;
/**
 * Takes hex string or Uint8Array, converts to Uint8Array.
 * Validates output length.
 * Will throw error for other types.
 * @param title descriptive title for an error e.g. 'private key'
 * @param hex hex string or Uint8Array
 * @param expectedLength optional, will compare to result array's length
 * @returns
 */
export declare function ensureBytes(title: string, hex: Hex, expectedLength?: number): Uint8Array;
/**
 * Copies several Uint8Arrays into one.
 */
export declare function concatBytes(...arrays: Uint8Array[]): Uint8Array;
export declare function equalBytes(b1: Uint8Array, b2: Uint8Array): boolean;
/**
 * @example utf8ToBytes('abc') // new Uint8Array([97, 98, 99])
 */
export declare function utf8ToBytes(str: string): Uint8Array;
/**
 * Calculates amount of bits in a bigint.
 * Same as `n.toString(2).length`
 */
export declare function bitLen(n: bigint): number;
/**
 * Gets single bit at position.
 * NOTE: first bit position is 0 (same as arrays)
 * Same as `!!+Array.from(n.toString(2)).reverse()[pos]`
 */
export declare function bitGet(n: bigint, pos: number): bigint;
/**
 * Sets single bit at position.
 */
export declare const bitSet: (n: bigint, pos: number, value: boolean) => bigint;
/**
 * Calculate mask for N bits. Not using ** operator with bigints because of old engines.
 * Same as BigInt(`0b${Array(i).fill('1').join('')}`)
 */
export declare const bitMask: (n: number) => bigint;
type Pred<T> = (v: Uint8Array) => T | undefined;
/**
 * Minimal HMAC-DRBG from NIST 800-90 for RFC6979 sigs.
 * @returns function that will call DRBG until 2nd arg returns something meaningful
 * @example
 *   const drbg = createHmacDRBG<Key>(32, 32, hmac);
 *   drbg(seed, bytesToKey); // bytesToKey must return Key or undefined
 */
export declare function createHmacDrbg<T>(hashLen: number, qByteLen: number, hmacFn: (key: Uint8Array, ...messages: Uint8Array[]) => Uint8Array): (seed: Uint8Array, predicate: Pred<T>) => T;
declare const validatorFns: {
    readonly bigint: (val: any) => boolean;
    readonly function: (val: any) => boolean;
    readonly boolean: (val: any) => boolean;
    readonly string: (val: any) => boolean;
    readonly stringOrUint8Array: (val: any) => boolean;
    readonly isSafeInteger: (val: any) => boolean;
    readonly array: (val: any) => boolean;
    readonly field: (val: any, object: any) => any;
    readonly hash: (val: any) => boolean;
};
type Validator = keyof typeof validatorFns;
type ValMap<T extends Record<string, any>> = {
    [K in keyof T]?: Validator;
};
export declare function validateObject<T extends Record<string, any>>(object: T, validators: ValMap<T>, optValidators?: ValMap<T>): T;
export {};
//# sourceMappingURL=utils.d.ts.map