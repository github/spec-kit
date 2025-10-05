/**
 *  The **FixedNumber** class permits using values with decimal places,
 *  using fixed-pont math.
 *
 *  Fixed-point math is still based on integers under-the-hood, but uses an
 *  internal offset to store fractional components below, and each operation
 *  corrects for this after each operation.
 *
 *  @_section: api/utils/fixed-point-math:Fixed-Point Maths  [about-fixed-point-math]
 */
import { getBytes } from "./data.js";
import { assert, assertArgument, assertPrivate } from "./errors.js";
import {
    getBigInt, getNumber, fromTwos, mask, toBigInt
} from "./maths.js";
import { defineProperties } from "./properties.js";

import type { BigNumberish, BytesLike, Numeric } from "./index.js";

const BN_N1 = BigInt(-1);
const BN_0 = BigInt(0);
const BN_1 = BigInt(1);
const BN_5 = BigInt(5);

const _guard = { };


// Constant to pull zeros from for multipliers
let Zeros = "0000";
while (Zeros.length < 80) { Zeros += Zeros; }

// Returns a string "1" followed by decimal "0"s
function getTens(decimals: number): bigint {
    let result = Zeros;
    while (result.length < decimals) { result += result; }
    return BigInt("1" + result.substring(0, decimals));
}



    /*
     *  Returns a new FixedFormat for %%value%%.
     *
     *  If %%value%% is specified as a ``number``, the bit-width is
     *  128 bits and %%value%% is used for the ``decimals``.
     *
     *  A string %%value%% may begin with ``fixed`` or ``ufixed``
     *  for signed and unsigned respectfully. If no other properties
     *  are specified, the bit-width is 128-bits with 18 decimals.
     *
     *  To specify the bit-width and demicals, append them separated
     *  by an ``"x"`` to the %%value%%.
     *
     *  For example, ``ufixed128x18`` describes an unsigned, 128-bit
     *  wide format with 18 decimals.
     *
     *  If %%value%% is an other object, its properties for ``signed``,
     *  ``width`` and ``decimals`` are checked.
     */

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
    signed?: boolean,
    width?: number,
    decimals?: number
};

function checkValue(val: bigint, format: _FixedFormat, safeOp?: string): bigint {
    const width = BigInt(format.width);
    if (format.signed) {
        const limit = (BN_1 << (width - BN_1));
        assert(safeOp == null || (val >= -limit  && val < limit), "overflow", "NUMERIC_FAULT", {
            operation: <string>safeOp, fault: "overflow", value: val
        });

        if (val > BN_0) {
            val = fromTwos(mask(val, width), width);
        } else {
            val = -fromTwos(mask(-val, width), width);
        }

    } else {
        const limit = (BN_1 << width);
        assert(safeOp == null || (val >= 0 && val < limit), "overflow", "NUMERIC_FAULT", {
            operation: <string>safeOp, fault: "overflow", value: val
        });
        val = (((val % limit) + limit) % limit) & (limit - BN_1);
    }

    return val;
}

type _FixedFormat = { signed: boolean, width: number, decimals: number, name: string }

function getFormat(value?: FixedFormat): _FixedFormat {
    if (typeof(value) === "number") { value = `fixed128x${value}` }

    let signed = true;
    let width = 128;
    let decimals = 18;

    if (typeof(value) === "string") {
        // Parse the format string
        if (value === "fixed") {
            // defaults...
        } else if (value === "ufixed") {
            signed = false;
        } else {
            const match = value.match(/^(u?)fixed([0-9]+)x([0-9]+)$/);
            assertArgument(match, "invalid fixed format", "format", value);
            signed = (match[1] !== "u");
            width = parseInt(match[2]);
            decimals = parseInt(match[3]);
        }
    } else if (value) {
        // Extract the values from the object
        const v: any = value;
        const check = (key: string, type: string, defaultValue: any): any => {
            if (v[key] == null) { return defaultValue; }
            assertArgument(typeof(v[key]) === type,
                "invalid fixed format (" + key + " not " + type +")", "format." + key, v[key]);
            return v[key];
        }
        signed = check("signed", "boolean", signed);
        width = check("width", "number", width);
        decimals = check("decimals", "number", decimals);
    }

    assertArgument((width % 8) === 0, "invalid FixedNumber width (not byte aligned)", "format.width", width);
    assertArgument(decimals <= 80, "invalid FixedNumber decimals (too large)", "format.decimals", decimals);

    const name = (signed ? "": "u") + "fixed" + String(width) + "x" + String(decimals);

    return { signed, width, decimals, name };
}

function toString(val: bigint, decimals: number) {
    let negative = "";
    if (val < BN_0) {
        negative = "-";
        val *= BN_N1;
    }

    let str = val.toString();

    // No decimal point for whole values
    if (decimals === 0) { return (negative + str); }

    // Pad out to the whole component (including a whole digit)
    while (str.length <= decimals) { str = Zeros + str; }

    // Insert the decimal point
    const index = str.length - decimals;
    str = str.substring(0, index) + "." + str.substring(index);

    // Trim the whole component (leaving at least one 0)
    while (str[0] === "0" && str[1] !== ".") {
        str = str.substring(1);
    }

    // Trim the decimal component (leaving at least one 0)
    while (str[str.length - 1] === "0" && str[str.length - 2] !== ".") {
        str = str.substring(0, str.length - 1);
    }

    return (negative + str);
}


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
export class FixedNumber {

    /**
     *  The specific fixed-point arithmetic field for this value.
     */
    readonly format!: string;

    readonly #format: _FixedFormat;

    // The actual value (accounting for decimals)
    #val: bigint;

    // A base-10 value to multiple values by to maintain the magnitude
    readonly #tens: bigint;

    /**
     *  This is a property so console.log shows a human-meaningful value.
     *
     *  @private
     */
    readonly _value!: string;

    // Use this when changing this file to get some typing info,
    // but then switch to any to mask the internal type
    //constructor(guard: any, value: bigint, format: _FixedFormat) {

    /**
     *  @private
     */
    constructor(guard: any, value: bigint, format: any) {
        assertPrivate(guard, _guard, "FixedNumber");

        this.#val = value;

        this.#format = format;

        const _value = toString(value, format.decimals);

        defineProperties<FixedNumber>(this, { format: format.name, _value });

        this.#tens = getTens(format.decimals);
    }

    /**
     *  If true, negative values are permitted, otherwise only
     *  positive values and zero are allowed.
     */
    get signed(): boolean { return this.#format.signed; }

    /**
     *  The number of bits available to store the value.
     */
    get width(): number { return this.#format.width; }

    /**
     *  The number of decimal places in the fixed-point arithment field.
     */
    get decimals(): number { return this.#format.decimals; }

    /**
     *  The value as an integer, based on the smallest unit the
     *  [[decimals]] allow.
     */
    get value(): bigint { return this.#val; }

    #checkFormat(other: FixedNumber): void {
        assertArgument(this.format === other.format,
            "incompatible format; use fixedNumber.toFormat", "other", other);
    }

    #checkValue(val: bigint, safeOp?: string): FixedNumber {
/*
        const width = BigInt(this.width);
        if (this.signed) {
            const limit = (BN_1 << (width - BN_1));
            assert(safeOp == null || (val >= -limit  && val < limit), "overflow", "NUMERIC_FAULT", {
                operation: <string>safeOp, fault: "overflow", value: val
            });

            if (val > BN_0) {
                val = fromTwos(mask(val, width), width);
            } else {
                val = -fromTwos(mask(-val, width), width);
            }

        } else {
            const masked = mask(val, width);
            assert(safeOp == null || (val >= 0 && val === masked), "overflow", "NUMERIC_FAULT", {
                operation: <string>safeOp, fault: "overflow", value: val
            });
            val = masked;
        }
*/
        val = checkValue(val, this.#format, safeOp);
        return new FixedNumber(_guard, val, this.#format);
    }

    #add(o: FixedNumber, safeOp?: string): FixedNumber {
        this.#checkFormat(o);
        return this.#checkValue(this.#val + o.#val, safeOp);
    }

    /**
     *  Returns a new [[FixedNumber]] with the result of %%this%% added
     *  to %%other%%, ignoring overflow.
     */
    addUnsafe(other: FixedNumber): FixedNumber { return this.#add(other); }

    /**
     *  Returns a new [[FixedNumber]] with the result of %%this%% added
     *  to %%other%%. A [[NumericFaultError]] is thrown if overflow
     *  occurs.
     */
    add(other: FixedNumber): FixedNumber { return this.#add(other, "add"); }

    #sub(o: FixedNumber, safeOp?: string): FixedNumber {
        this.#checkFormat(o);
        return this.#checkValue(this.#val - o.#val, safeOp);
    }

    /**
     *  Returns a new [[FixedNumber]] with the result of %%other%% subtracted
     *  from %%this%%, ignoring overflow.
     */
    subUnsafe(other: FixedNumber): FixedNumber { return this.#sub(other); }

    /**
     *  Returns a new [[FixedNumber]] with the result of %%other%% subtracted
     *  from %%this%%. A [[NumericFaultError]] is thrown if overflow
     *  occurs.
     */
    sub(other: FixedNumber): FixedNumber { return this.#sub(other, "sub"); }

    #mul(o: FixedNumber, safeOp?: string): FixedNumber {
        this.#checkFormat(o);
        return this.#checkValue((this.#val * o.#val) / this.#tens, safeOp);
    }

    /**
     *  Returns a new [[FixedNumber]] with the result of %%this%% multiplied
     *  by %%other%%, ignoring overflow and underflow (precision loss).
     */
    mulUnsafe(other: FixedNumber): FixedNumber { return this.#mul(other); }

    /**
     *  Returns a new [[FixedNumber]] with the result of %%this%% multiplied
     *  by %%other%%. A [[NumericFaultError]] is thrown if overflow
     *  occurs.
     */
    mul(other: FixedNumber): FixedNumber { return this.#mul(other, "mul"); }

    /**
     *  Returns a new [[FixedNumber]] with the result of %%this%% multiplied
     *  by %%other%%. A [[NumericFaultError]] is thrown if overflow
     *  occurs or if underflow (precision loss) occurs.
     */
    mulSignal(other: FixedNumber): FixedNumber {
        this.#checkFormat(other);
        const value = this.#val * other.#val;
        assert((value % this.#tens) === BN_0, "precision lost during signalling mul", "NUMERIC_FAULT", {
            operation: "mulSignal", fault: "underflow", value: this
        });
        return this.#checkValue(value / this.#tens, "mulSignal");
    }

    #div(o: FixedNumber, safeOp?: string): FixedNumber {
        assert(o.#val !== BN_0, "division by zero", "NUMERIC_FAULT", {
            operation: "div", fault: "divide-by-zero", value: this
        });
        this.#checkFormat(o);
        return this.#checkValue((this.#val * this.#tens) / o.#val, safeOp);
    }

    /**
     *  Returns a new [[FixedNumber]] with the result of %%this%% divided
     *  by %%other%%, ignoring underflow (precision loss). A
     *  [[NumericFaultError]] is thrown if overflow occurs.
     */
    divUnsafe(other: FixedNumber): FixedNumber { return this.#div(other); }

    /**
     *  Returns a new [[FixedNumber]] with the result of %%this%% divided
     *  by %%other%%, ignoring underflow (precision loss). A
     *  [[NumericFaultError]] is thrown if overflow occurs.
     */
    div(other: FixedNumber): FixedNumber { return this.#div(other, "div"); }


    /**
     *  Returns a new [[FixedNumber]] with the result of %%this%% divided
     *  by %%other%%. A [[NumericFaultError]] is thrown if underflow
     *  (precision loss) occurs.
     */
    divSignal(other: FixedNumber): FixedNumber {
        assert(other.#val !== BN_0, "division by zero", "NUMERIC_FAULT", {
            operation: "div", fault: "divide-by-zero", value: this
        });
        this.#checkFormat(other);
        const value = (this.#val * this.#tens);
        assert((value % other.#val) === BN_0, "precision lost during signalling div", "NUMERIC_FAULT", {
            operation: "divSignal", fault: "underflow", value: this
        });
        return this.#checkValue(value / other.#val, "divSignal");
    }

    /**
     *  Returns a comparison result between %%this%% and %%other%%.
     *
     *  This is suitable for use in sorting, where ``-1`` implies %%this%%
     *  is smaller, ``1`` implies %%this%% is larger and ``0`` implies
     *  both are equal.
     */
     cmp(other: FixedNumber): number {
         let a = this.value, b = other.value;

         // Coerce a and b to the same magnitude
         const delta = this.decimals - other.decimals;
         if (delta > 0) {
             b *= getTens(delta);
         } else if (delta < 0) {
             a *= getTens(-delta);
         }

         // Comnpare
         if (a < b) { return -1; }
         if (a > b) { return 1; }
         return 0;
     }

    /**
     *  Returns true if %%other%% is equal to %%this%%.
     */
     eq(other: FixedNumber): boolean { return this.cmp(other) === 0; }

    /**
     *  Returns true if %%other%% is less than to %%this%%.
     */
     lt(other: FixedNumber): boolean { return this.cmp(other) < 0; }

    /**
     *  Returns true if %%other%% is less than or equal to %%this%%.
     */
     lte(other: FixedNumber): boolean { return this.cmp(other) <= 0; }

    /**
     *  Returns true if %%other%% is greater than to %%this%%.
     */
     gt(other: FixedNumber): boolean { return this.cmp(other) > 0; }

    /**
     *  Returns true if %%other%% is greater than or equal to %%this%%.
     */
     gte(other: FixedNumber): boolean { return this.cmp(other) >= 0; }

    /**
     *  Returns a new [[FixedNumber]] which is the largest **integer**
     *  that is less than or equal to %%this%%.
     *
     *  The decimal component of the result will always be ``0``.
     */
    floor(): FixedNumber {
        let val = this.#val;
        if (this.#val < BN_0) { val -= this.#tens - BN_1; }
        val = (this.#val / this.#tens) * this.#tens;
        return this.#checkValue(val, "floor");
    }

    /**
     *  Returns a new [[FixedNumber]] which is the smallest **integer**
     *  that is greater than or equal to %%this%%.
     *
     *  The decimal component of the result will always be ``0``.
     */
    ceiling(): FixedNumber {
        let val = this.#val;
        if (this.#val > BN_0) { val += this.#tens - BN_1; }
        val = (this.#val / this.#tens) * this.#tens;
        return this.#checkValue(val, "ceiling");
    }

    /**
     *  Returns a new [[FixedNumber]] with the decimal component
     *  rounded up on ties at %%decimals%% places.
     */
    round(decimals?: number): FixedNumber {
        if (decimals == null) { decimals = 0; }

        // Not enough precision to not already be rounded
        if (decimals >= this.decimals) { return this; }

        const delta = this.decimals - decimals;
        const bump = BN_5 * getTens(delta - 1);

        let value = this.value + bump;
        const tens = getTens(delta);
        value = (value / tens) * tens;

        checkValue(value, this.#format, "round");

        return new FixedNumber(_guard, value, this.#format);
    }

    /**
     *  Returns true if %%this%% is equal to ``0``.
     */
    isZero(): boolean { return (this.#val === BN_0); }

    /**
     *  Returns true if %%this%% is less than ``0``.
     */
    isNegative(): boolean { return (this.#val < BN_0); }

    /**
     *  Returns the string representation of %%this%%.
     */
    toString(): string { return this._value; }

    /**
     *  Returns a float approximation.
     *
     *  Due to IEEE 754 precission (or lack thereof), this function
     *  can only return an approximation and most values will contain
     *  rounding errors.
     */
    toUnsafeFloat(): number { return parseFloat(this.toString()); }

    /**
     *  Return a new [[FixedNumber]] with the same value but has had
     *  its field set to %%format%%.
     *
     *  This will throw if the value cannot fit into %%format%%.
     */
    toFormat(format: FixedFormat): FixedNumber {
        return FixedNumber.fromString(this.toString(), format);
    }

    /**
     *  Creates a new [[FixedNumber]] for %%value%% divided by
     *  %%decimal%% places with %%format%%.
     *
     *  This will throw a [[NumericFaultError]] if %%value%% (once adjusted
     *  for %%decimals%%) cannot fit in %%format%%, either due to overflow
     *  or underflow (precision loss).
     */
    static fromValue(_value: BigNumberish, _decimals?: Numeric, _format?: FixedFormat): FixedNumber {
        const decimals = (_decimals == null) ? 0: getNumber(_decimals);
        const format = getFormat(_format);

        let value = getBigInt(_value, "value");
        const delta = decimals - format.decimals;
        if (delta > 0) {
            const tens = getTens(delta);
            assert((value % tens) === BN_0, "value loses precision for format", "NUMERIC_FAULT", {
                operation: "fromValue", fault: "underflow", value: _value
            });
            value /= tens;
        } else if (delta < 0) {
            value *= getTens(-delta);
        }

        checkValue(value, format, "fromValue");

        return new FixedNumber(_guard, value, format);
    }

    /**
     *  Creates a new [[FixedNumber]] for %%value%% with %%format%%.
     *
     *  This will throw a [[NumericFaultError]] if %%value%% cannot fit
     *  in %%format%%, either due to overflow or underflow (precision loss).
     */
    static fromString(_value: string, _format?: FixedFormat): FixedNumber {
        const match = _value.match(/^(-?)([0-9]*)\.?([0-9]*)$/);
        assertArgument(match && (match[2].length + match[3].length) > 0, "invalid FixedNumber string value", "value", _value);

        const format = getFormat(_format);

        let whole = (match[2] || "0"), decimal = (match[3] || "");

        // Pad out the decimals
        while (decimal.length < format.decimals) { decimal += Zeros; }

        // Check precision is safe
        assert(decimal.substring(format.decimals).match(/^0*$/), "too many decimals for format", "NUMERIC_FAULT", {
            operation: "fromString", fault: "underflow", value: _value
        });

        // Remove extra padding
        decimal = decimal.substring(0, format.decimals);

        const value = BigInt(match[1] + whole + decimal)

        checkValue(value, format, "fromString");

        return new FixedNumber(_guard, value, format);
    }

    /**
     *  Creates a new [[FixedNumber]] with the big-endian representation
     *  %%value%% with %%format%%.
     *
     *  This will throw a [[NumericFaultError]] if %%value%% cannot fit
     *  in %%format%% due to overflow.
     */
    static fromBytes(_value: BytesLike, _format?: FixedFormat): FixedNumber {
        let value = toBigInt(getBytes(_value, "value"));
        const format = getFormat(_format);

        if (format.signed) { value = fromTwos(value, format.width); }

        checkValue(value, format, "fromBytes");

        return new FixedNumber(_guard, value, format);
    }
}

//const f1 = FixedNumber.fromString("12.56", "fixed16x2");
//const f2 = FixedNumber.fromString("0.3", "fixed16x2");
//console.log(f1.divSignal(f2));
//const BUMP = FixedNumber.from("0.5");
