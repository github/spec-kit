/**
 *  A Typed object allows a value to have its type explicitly
 *  specified.
 *
 *  For example, in Solidity, the value ``45`` could represent a
 *  ``uint8`` or a ``uint256``. The value ``0x1234`` could represent
 *  a ``bytes2`` or ``bytes``.
 *
 *  Since JavaScript has no meaningful way to explicitly inform any
 *  APIs which what the type is, this allows transparent interoperation
 *  with Soldity.
 *
 *  @_subsection: api/abi:Typed Values
 */
import type { Addressable } from "../address/index.js";
import type { BigNumberish, BytesLike } from "../utils/index.js";
import type { Result } from "./coders/abstract-coder.js";
/**
 *  @_ignore:
 */
export interface TypedNumber extends Typed {
    value: number;
    defaultValue(): number;
    minValue(): number;
    maxValue(): number;
}
/**
 *  A **Typed** that represents a numeric value.
 */
export interface TypedBigInt extends Typed {
    /**
     *  The value.
     */
    value: bigint;
    /**
     *  The default value for all numeric types is ``0``.
     */
    defaultValue(): bigint;
    /**
     *  The minimum value for this type, accounting for bit-width and signed-ness.
     */
    minValue(): bigint;
    /**
     *  The minimum value for this type, accounting for bit-width.
     */
    maxValue(): bigint;
}
/**
 *  A **Typed** that represents a binary sequence of data as bytes.
 */
export interface TypedData extends Typed {
    /**
     *  The value.
     */
    value: string;
    /**
     *  The default value for this type.
     */
    defaultValue(): string;
}
/**
 *  A **Typed** that represents a UTF-8 sequence of bytes.
 */
export interface TypedString extends Typed {
    /**
     *  The value.
     */
    value: string;
    /**
     *  The default value for the string type is the empty string (i.e. ``""``).
     */
    defaultValue(): string;
}
/**
 *  The **Typed** class to wrap values providing explicit type information.
 */
export declare class Typed {
    #private;
    /**
     *  The type, as a Solidity-compatible type.
     */
    readonly type: string;
    /**
     *  The actual value.
     */
    readonly value: any;
    /**
     *  @_ignore:
     */
    readonly _typedSymbol: Symbol;
    /**
     *  @_ignore:
     */
    constructor(gaurd: any, type: string, value: any, options?: any);
    /**
     *  Format the type as a Human-Readable type.
     */
    format(): string;
    /**
     *  The default value returned by this type.
     */
    defaultValue(): string | number | bigint | Result;
    /**
     *  The minimum value for numeric types.
     */
    minValue(): string | number | bigint;
    /**
     *  The maximum value for numeric types.
     */
    maxValue(): string | number | bigint;
    /**
     *  Returns ``true`` and provides a type guard is this is a [[TypedBigInt]].
     */
    isBigInt(): this is TypedBigInt;
    /**
     *  Returns ``true`` and provides a type guard is this is a [[TypedData]].
     */
    isData(): this is TypedData;
    /**
     *  Returns ``true`` and provides a type guard is this is a [[TypedString]].
     */
    isString(): this is TypedString;
    /**
     *  Returns the tuple name, if this is a tuple. Throws otherwise.
     */
    get tupleName(): null | string;
    /**
     *  Returns the length of the array type or ``-1`` if it is dynamic.
     *
     *  Throws if the type is not an array.
     */
    get arrayLength(): null | number;
    /**
     *  Returns a new **Typed** of %%type%% with the %%value%%.
     */
    static from(type: string, value: any): Typed;
    /**
     *  Return a new ``uint8`` type for %%v%%.
     */
    static uint8(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint16`` type for %%v%%.
     */
    static uint16(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint24`` type for %%v%%.
     */
    static uint24(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint32`` type for %%v%%.
     */
    static uint32(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint40`` type for %%v%%.
     */
    static uint40(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint48`` type for %%v%%.
     */
    static uint48(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint56`` type for %%v%%.
     */
    static uint56(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint64`` type for %%v%%.
     */
    static uint64(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint72`` type for %%v%%.
     */
    static uint72(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint80`` type for %%v%%.
     */
    static uint80(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint88`` type for %%v%%.
     */
    static uint88(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint96`` type for %%v%%.
     */
    static uint96(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint104`` type for %%v%%.
     */
    static uint104(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint112`` type for %%v%%.
     */
    static uint112(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint120`` type for %%v%%.
     */
    static uint120(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint128`` type for %%v%%.
     */
    static uint128(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint136`` type for %%v%%.
     */
    static uint136(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint144`` type for %%v%%.
     */
    static uint144(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint152`` type for %%v%%.
     */
    static uint152(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint160`` type for %%v%%.
     */
    static uint160(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint168`` type for %%v%%.
     */
    static uint168(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint176`` type for %%v%%.
     */
    static uint176(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint184`` type for %%v%%.
     */
    static uint184(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint192`` type for %%v%%.
     */
    static uint192(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint200`` type for %%v%%.
     */
    static uint200(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint208`` type for %%v%%.
     */
    static uint208(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint216`` type for %%v%%.
     */
    static uint216(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint224`` type for %%v%%.
     */
    static uint224(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint232`` type for %%v%%.
     */
    static uint232(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint240`` type for %%v%%.
     */
    static uint240(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint248`` type for %%v%%.
     */
    static uint248(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint256`` type for %%v%%.
     */
    static uint256(v: BigNumberish): Typed;
    /**
     *  Return a new ``uint256`` type for %%v%%.
     */
    static uint(v: BigNumberish): Typed;
    /**
     *  Return a new ``int8`` type for %%v%%.
     */
    static int8(v: BigNumberish): Typed;
    /**
     *  Return a new ``int16`` type for %%v%%.
     */
    static int16(v: BigNumberish): Typed;
    /**
     *  Return a new ``int24`` type for %%v%%.
     */
    static int24(v: BigNumberish): Typed;
    /**
     *  Return a new ``int32`` type for %%v%%.
     */
    static int32(v: BigNumberish): Typed;
    /**
     *  Return a new ``int40`` type for %%v%%.
     */
    static int40(v: BigNumberish): Typed;
    /**
     *  Return a new ``int48`` type for %%v%%.
     */
    static int48(v: BigNumberish): Typed;
    /**
     *  Return a new ``int56`` type for %%v%%.
     */
    static int56(v: BigNumberish): Typed;
    /**
     *  Return a new ``int64`` type for %%v%%.
     */
    static int64(v: BigNumberish): Typed;
    /**
     *  Return a new ``int72`` type for %%v%%.
     */
    static int72(v: BigNumberish): Typed;
    /**
     *  Return a new ``int80`` type for %%v%%.
     */
    static int80(v: BigNumberish): Typed;
    /**
     *  Return a new ``int88`` type for %%v%%.
     */
    static int88(v: BigNumberish): Typed;
    /**
     *  Return a new ``int96`` type for %%v%%.
     */
    static int96(v: BigNumberish): Typed;
    /**
     *  Return a new ``int104`` type for %%v%%.
     */
    static int104(v: BigNumberish): Typed;
    /**
     *  Return a new ``int112`` type for %%v%%.
     */
    static int112(v: BigNumberish): Typed;
    /**
     *  Return a new ``int120`` type for %%v%%.
     */
    static int120(v: BigNumberish): Typed;
    /**
     *  Return a new ``int128`` type for %%v%%.
     */
    static int128(v: BigNumberish): Typed;
    /**
     *  Return a new ``int136`` type for %%v%%.
     */
    static int136(v: BigNumberish): Typed;
    /**
     *  Return a new ``int144`` type for %%v%%.
     */
    static int144(v: BigNumberish): Typed;
    /**
     *  Return a new ``int52`` type for %%v%%.
     */
    static int152(v: BigNumberish): Typed;
    /**
     *  Return a new ``int160`` type for %%v%%.
     */
    static int160(v: BigNumberish): Typed;
    /**
     *  Return a new ``int168`` type for %%v%%.
     */
    static int168(v: BigNumberish): Typed;
    /**
     *  Return a new ``int176`` type for %%v%%.
     */
    static int176(v: BigNumberish): Typed;
    /**
     *  Return a new ``int184`` type for %%v%%.
     */
    static int184(v: BigNumberish): Typed;
    /**
     *  Return a new ``int92`` type for %%v%%.
     */
    static int192(v: BigNumberish): Typed;
    /**
     *  Return a new ``int200`` type for %%v%%.
     */
    static int200(v: BigNumberish): Typed;
    /**
     *  Return a new ``int208`` type for %%v%%.
     */
    static int208(v: BigNumberish): Typed;
    /**
     *  Return a new ``int216`` type for %%v%%.
     */
    static int216(v: BigNumberish): Typed;
    /**
     *  Return a new ``int224`` type for %%v%%.
     */
    static int224(v: BigNumberish): Typed;
    /**
     *  Return a new ``int232`` type for %%v%%.
     */
    static int232(v: BigNumberish): Typed;
    /**
     *  Return a new ``int240`` type for %%v%%.
     */
    static int240(v: BigNumberish): Typed;
    /**
     *  Return a new ``int248`` type for %%v%%.
     */
    static int248(v: BigNumberish): Typed;
    /**
     *  Return a new ``int256`` type for %%v%%.
     */
    static int256(v: BigNumberish): Typed;
    /**
     *  Return a new ``int256`` type for %%v%%.
     */
    static int(v: BigNumberish): Typed;
    /**
     *  Return a new ``bytes1`` type for %%v%%.
     */
    static bytes1(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes2`` type for %%v%%.
     */
    static bytes2(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes3`` type for %%v%%.
     */
    static bytes3(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes4`` type for %%v%%.
     */
    static bytes4(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes5`` type for %%v%%.
     */
    static bytes5(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes6`` type for %%v%%.
     */
    static bytes6(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes7`` type for %%v%%.
     */
    static bytes7(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes8`` type for %%v%%.
     */
    static bytes8(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes9`` type for %%v%%.
     */
    static bytes9(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes10`` type for %%v%%.
     */
    static bytes10(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes11`` type for %%v%%.
     */
    static bytes11(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes12`` type for %%v%%.
     */
    static bytes12(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes13`` type for %%v%%.
     */
    static bytes13(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes14`` type for %%v%%.
     */
    static bytes14(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes15`` type for %%v%%.
     */
    static bytes15(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes16`` type for %%v%%.
     */
    static bytes16(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes17`` type for %%v%%.
     */
    static bytes17(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes18`` type for %%v%%.
     */
    static bytes18(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes19`` type for %%v%%.
     */
    static bytes19(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes20`` type for %%v%%.
     */
    static bytes20(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes21`` type for %%v%%.
     */
    static bytes21(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes22`` type for %%v%%.
     */
    static bytes22(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes23`` type for %%v%%.
     */
    static bytes23(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes24`` type for %%v%%.
     */
    static bytes24(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes25`` type for %%v%%.
     */
    static bytes25(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes26`` type for %%v%%.
     */
    static bytes26(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes27`` type for %%v%%.
     */
    static bytes27(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes28`` type for %%v%%.
     */
    static bytes28(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes29`` type for %%v%%.
     */
    static bytes29(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes30`` type for %%v%%.
     */
    static bytes30(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes31`` type for %%v%%.
     */
    static bytes31(v: BytesLike): Typed;
    /**
     *  Return a new ``bytes32`` type for %%v%%.
     */
    static bytes32(v: BytesLike): Typed;
    /**
     *  Return a new ``address`` type for %%v%%.
     */
    static address(v: string | Addressable): Typed;
    /**
     *  Return a new ``bool`` type for %%v%%.
     */
    static bool(v: any): Typed;
    /**
     *  Return a new ``bytes`` type for %%v%%.
     */
    static bytes(v: BytesLike): Typed;
    /**
     *  Return a new ``string`` type for %%v%%.
     */
    static string(v: string): Typed;
    /**
     *  Return a new ``array`` type for %%v%%, allowing %%dynamic%% length.
     */
    static array(v: Array<any | Typed>, dynamic?: null | boolean): Typed;
    /**
     *  Return a new ``tuple`` type for %%v%%, with the optional %%name%%.
     */
    static tuple(v: Array<any | Typed> | Record<string, any | Typed>, name?: string): Typed;
    /**
     *  Return a new ``uint8`` type for %%v%%.
     */
    static overrides(v: Record<string, any>): Typed;
    /**
     *  Returns true only if %%value%% is a [[Typed]] instance.
     */
    static isTyped(value: any): value is Typed;
    /**
     *  If the value is a [[Typed]] instance, validates the underlying value
     *  and returns it, otherwise returns value directly.
     *
     *  This is useful for functions that with to accept either a [[Typed]]
     *  object or values.
     */
    static dereference<T>(value: Typed | T, type: string): T;
}
//# sourceMappingURL=typed.d.ts.map