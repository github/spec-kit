import type { BytesLike } from "./data.js";
/**
 *  Any type that can be used where a numeric value is needed.
 */
export type Numeric = number | bigint;
/**
 *  Any type that can be used where a big number is needed.
 */
export type BigNumberish = string | Numeric;
/**
 *  Convert %%value%% from a twos-compliment representation of %%width%%
 *  bits to its value.
 *
 *  If the highest bit is ``1``, the result will be negative.
 */
export declare function fromTwos(_value: BigNumberish, _width: Numeric): bigint;
/**
 *  Convert %%value%% to a twos-compliment representation of
 *  %%width%% bits.
 *
 *  The result will always be positive.
 */
export declare function toTwos(_value: BigNumberish, _width: Numeric): bigint;
/**
 *  Mask %%value%% with a bitmask of %%bits%% ones.
 */
export declare function mask(_value: BigNumberish, _bits: Numeric): bigint;
/**
 *  Gets a BigInt from %%value%%. If it is an invalid value for
 *  a BigInt, then an ArgumentError will be thrown for %%name%%.
 */
export declare function getBigInt(value: BigNumberish, name?: string): bigint;
/**
 *  Returns %%value%% as a bigint, validating it is valid as a bigint
 *  value and that it is positive.
 */
export declare function getUint(value: BigNumberish, name?: string): bigint;
export declare function toBigInt(value: BigNumberish | Uint8Array): bigint;
/**
 *  Gets a //number// from %%value%%. If it is an invalid value for
 *  a //number//, then an ArgumentError will be thrown for %%name%%.
 */
export declare function getNumber(value: BigNumberish, name?: string): number;
/**
 *  Converts %%value%% to a number. If %%value%% is a Uint8Array, it
 *  is treated as Big Endian data. Throws if the value is not safe.
 */
export declare function toNumber(value: BigNumberish | Uint8Array): number;
/**
 *  Converts %%value%% to a Big Endian hexstring, optionally padded to
 *  %%width%% bytes.
 */
export declare function toBeHex(_value: BigNumberish, _width?: Numeric): string;
/**
 *  Converts %%value%% to a Big Endian Uint8Array.
 */
export declare function toBeArray(_value: BigNumberish): Uint8Array;
/**
 *  Returns a [[HexString]] for %%value%% safe to use as a //Quantity//.
 *
 *  A //Quantity// does not have and leading 0 values unless the value is
 *  the literal value `0x0`. This is most commonly used for JSSON-RPC
 *  numeric values.
 */
export declare function toQuantity(value: BytesLike | BigNumberish): string;
//# sourceMappingURL=maths.d.ts.map