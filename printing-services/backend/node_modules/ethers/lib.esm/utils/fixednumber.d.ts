import type { BigNumberish, BytesLike, Numeric } from "./index.js";
/**
 *  A description of a fixed-point arithmetic field.
 *
 *  When specifying the fixed format, the values override the default of
 *  a ``fixed128x18``, which implies a signed 128-bit value with 18
 *  decimals of precision.
 *
 *  The alias ``fixed`` and ``ufixed`` can be used for ``fixed128x18`` and
 *  ``ufixed128x18`` respectively.
 *
 *  When a fixed format string begins with a ``u``, it indicates the field
 *  is unsigned, so any negative values will overflow. The first number
 *  indicates the bit-width and the second number indicates the decimal
 *  precision.
 *
 *  When a ``number`` is used for a fixed format, it indicates the number
 *  of decimal places, and the default width and signed-ness will be used.
 *
 *  The bit-width must be byte aligned and the decimals can be at most 80.
 */
export type FixedFormat = number | string | {
    signed?: boolean;
    width?: number;
    decimals?: number;
};
/**
 *  A FixedNumber represents a value over its [[FixedFormat]]
 *  arithmetic field.
 *
 *  A FixedNumber can be used to perform math, losslessly, on
 *  values which have decmial places.
 *
 *  A FixedNumber has a fixed bit-width to store values in, and stores all
 *  values internally by multiplying the value by 10 raised to the power of
 *  %%decimals%%.
 *
 *  If operations are performed that cause a value to grow too high (close to
 *  positive infinity) or too low (close to negative infinity), the value
 *  is said to //overflow//.
 *
 *  For example, an 8-bit signed value, with 0 decimals may only be within
 *  the range ``-128`` to ``127``; so ``-128 - 1`` will overflow and become
 *  ``127``. Likewise, ``127 + 1`` will overflow and become ``-127``.
 *
 *  Many operation have a normal and //unsafe// variant. The normal variant
 *  will throw a [[NumericFaultError]] on any overflow, while the //unsafe//
 *  variant will silently allow overflow, corrupting its value value.
 *
 *  If operations are performed that cause a value to become too small
 *  (close to zero), the value loses precison and is said to //underflow//.
 *
 *  For example, a value with 1 decimal place may store a number as small
 *  as ``0.1``, but the value of ``0.1 / 2`` is ``0.05``, which cannot fit
 *  into 1 decimal place, so underflow occurs which means precision is lost
 *  and the value becomes ``0``.
 *
 *  Some operations have a normal and //signalling// variant. The normal
 *  variant will silently ignore underflow, while the //signalling// variant
 *  will thow a [[NumericFaultError]] on underflow.
 */
export declare class FixedNumber {
    #private;
    /**
     *  The specific fixed-point arithmetic field for this value.
     */
    readonly format: string;
    /**
     *  This is a property so console.log shows a human-meaningful value.
     *
     *  @private
     */
    readonly _value: string;
    /**
     *  @private
     */
    constructor(guard: any, value: bigint, format: any);
    /**
     *  If true, negative values are permitted, otherwise only
     *  positive values and zero are allowed.
     */
    get signed(): boolean;
    /**
     *  The number of bits available to store the value.
     */
    get width(): number;
    /**
     *  The number of decimal places in the fixed-point arithment field.
     */
    get decimals(): number;
    /**
     *  The value as an integer, based on the smallest unit the
     *  [[decimals]] allow.
     */
    get value(): bigint;
    /**
     *  Returns a new [[FixedNumber]] with the result of %%this%% added
     *  to %%other%%, ignoring overflow.
     */
    addUnsafe(other: FixedNumber): FixedNumber;
    /**
     *  Returns a new [[FixedNumber]] with the result of %%this%% added
     *  to %%other%%. A [[NumericFaultError]] is thrown if overflow
     *  occurs.
     */
    add(other: FixedNumber): FixedNumber;
    /**
     *  Returns a new [[FixedNumber]] with the result of %%other%% subtracted
     *  from %%this%%, ignoring overflow.
     */
    subUnsafe(other: FixedNumber): FixedNumber;
    /**
     *  Returns a new [[FixedNumber]] with the result of %%other%% subtracted
     *  from %%this%%. A [[NumericFaultError]] is thrown if overflow
     *  occurs.
     */
    sub(other: FixedNumber): FixedNumber;
    /**
     *  Returns a new [[FixedNumber]] with the result of %%this%% multiplied
     *  by %%other%%, ignoring overflow and underflow (precision loss).
     */
    mulUnsafe(other: FixedNumber): FixedNumber;
    /**
     *  Returns a new [[FixedNumber]] with the result of %%this%% multiplied
     *  by %%other%%. A [[NumericFaultError]] is thrown if overflow
     *  occurs.
     */
    mul(other: FixedNumber): FixedNumber;
    /**
     *  Returns a new [[FixedNumber]] with the result of %%this%% multiplied
     *  by %%other%%. A [[NumericFaultError]] is thrown if overflow
     *  occurs or if underflow (precision loss) occurs.
     */
    mulSignal(other: FixedNumber): FixedNumber;
    /**
     *  Returns a new [[FixedNumber]] with the result of %%this%% divided
     *  by %%other%%, ignoring underflow (precision loss). A
     *  [[NumericFaultError]] is thrown if overflow occurs.
     */
    divUnsafe(other: FixedNumber): FixedNumber;
    /**
     *  Returns a new [[FixedNumber]] with the result of %%this%% divided
     *  by %%other%%, ignoring underflow (precision loss). A
     *  [[NumericFaultError]] is thrown if overflow occurs.
     */
    div(other: FixedNumber): FixedNumber;
    /**
     *  Returns a new [[FixedNumber]] with the result of %%this%% divided
     *  by %%other%%. A [[NumericFaultError]] is thrown if underflow
     *  (precision loss) occurs.
     */
    divSignal(other: FixedNumber): FixedNumber;
    /**
     *  Returns a comparison result between %%this%% and %%other%%.
     *
     *  This is suitable for use in sorting, where ``-1`` implies %%this%%
     *  is smaller, ``1`` implies %%this%% is larger and ``0`` implies
     *  both are equal.
     */
    cmp(other: FixedNumber): number;
    /**
     *  Returns true if %%other%% is equal to %%this%%.
     */
    eq(other: FixedNumber): boolean;
    /**
     *  Returns true if %%other%% is less than to %%this%%.
     */
    lt(other: FixedNumber): boolean;
    /**
     *  Returns true if %%other%% is less than or equal to %%this%%.
     */
    lte(other: FixedNumber): boolean;
    /**
     *  Returns true if %%other%% is greater than to %%this%%.
     */
    gt(other: FixedNumber): boolean;
    /**
     *  Returns true if %%other%% is greater than or equal to %%this%%.
     */
    gte(other: FixedNumber): boolean;
    /**
     *  Returns a new [[FixedNumber]] which is the largest **integer**
     *  that is less than or equal to %%this%%.
     *
     *  The decimal component of the result will always be ``0``.
     */
    floor(): FixedNumber;
    /**
     *  Returns a new [[FixedNumber]] which is the smallest **integer**
     *  that is greater than or equal to %%this%%.
     *
     *  The decimal component of the result will always be ``0``.
     */
    ceiling(): FixedNumber;
    /**
     *  Returns a new [[FixedNumber]] with the decimal component
     *  rounded up on ties at %%decimals%% places.
     */
    round(decimals?: number): FixedNumber;
    /**
     *  Returns true if %%this%% is equal to ``0``.
     */
    isZero(): boolean;
    /**
     *  Returns true if %%this%% is less than ``0``.
     */
    isNegative(): boolean;
    /**
     *  Returns the string representation of %%this%%.
     */
    toString(): string;
    /**
     *  Returns a float approximation.
     *
     *  Due to IEEE 754 precission (or lack thereof), this function
     *  can only return an approximation and most values will contain
     *  rounding errors.
     */
    toUnsafeFloat(): number;
    /**
     *  Return a new [[FixedNumber]] with the same value but has had
     *  its field set to %%format%%.
     *
     *  This will throw if the value cannot fit into %%format%%.
     */
    toFormat(format: FixedFormat): FixedNumber;
    /**
     *  Creates a new [[FixedNumber]] for %%value%% divided by
     *  %%decimal%% places with %%format%%.
     *
     *  This will throw a [[NumericFaultError]] if %%value%% (once adjusted
     *  for %%decimals%%) cannot fit in %%format%%, either due to overflow
     *  or underflow (precision loss).
     */
    static fromValue(_value: BigNumberish, _decimals?: Numeric, _format?: FixedFormat): FixedNumber;
    /**
     *  Creates a new [[FixedNumber]] for %%value%% with %%format%%.
     *
     *  This will throw a [[NumericFaultError]] if %%value%% cannot fit
     *  in %%format%%, either due to overflow or underflow (precision loss).
     */
    static fromString(_value: string, _format?: FixedFormat): FixedNumber;
    /**
     *  Creates a new [[FixedNumber]] with the big-endian representation
     *  %%value%% with %%format%%.
     *
     *  This will throw a [[NumericFaultError]] if %%value%% cannot fit
     *  in %%format%% due to overflow.
     */
    static fromBytes(_value: BytesLike, _format?: FixedFormat): FixedNumber;
}
//# sourceMappingURL=fixednumber.d.ts.map