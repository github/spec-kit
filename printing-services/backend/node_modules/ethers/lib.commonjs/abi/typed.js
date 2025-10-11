"use strict";
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.Typed = void 0;
const index_js_1 = require("../utils/index.js");
const _gaurd = {};
function n(value, width) {
    let signed = false;
    if (width < 0) {
        signed = true;
        width *= -1;
    }
    // @TODO: Check range is valid for value
    return new Typed(_gaurd, `${signed ? "" : "u"}int${width}`, value, { signed, width });
}
function b(value, size) {
    // @TODO: Check range is valid for value
    return new Typed(_gaurd, `bytes${(size) ? size : ""}`, value, { size });
}
const _typedSymbol = Symbol.for("_ethers_typed");
/**
 *  The **Typed** class to wrap values providing explicit type information.
 */
class Typed {
    /**
     *  The type, as a Solidity-compatible type.
     */
    type;
    /**
     *  The actual value.
     */
    value;
    #options;
    /**
     *  @_ignore:
     */
    _typedSymbol;
    /**
     *  @_ignore:
     */
    constructor(gaurd, type, value, options) {
        if (options == null) {
            options = null;
        }
        (0, index_js_1.assertPrivate)(_gaurd, gaurd, "Typed");
        (0, index_js_1.defineProperties)(this, { _typedSymbol, type, value });
        this.#options = options;
        // Check the value is valid
        this.format();
    }
    /**
     *  Format the type as a Human-Readable type.
     */
    format() {
        if (this.type === "array") {
            throw new Error("");
        }
        else if (this.type === "dynamicArray") {
            throw new Error("");
        }
        else if (this.type === "tuple") {
            return `tuple(${this.value.map((v) => v.format()).join(",")})`;
        }
        return this.type;
    }
    /**
     *  The default value returned by this type.
     */
    defaultValue() {
        return 0;
    }
    /**
     *  The minimum value for numeric types.
     */
    minValue() {
        return 0;
    }
    /**
     *  The maximum value for numeric types.
     */
    maxValue() {
        return 0;
    }
    /**
     *  Returns ``true`` and provides a type guard is this is a [[TypedBigInt]].
     */
    isBigInt() {
        return !!(this.type.match(/^u?int[0-9]+$/));
    }
    /**
     *  Returns ``true`` and provides a type guard is this is a [[TypedData]].
     */
    isData() {
        return this.type.startsWith("bytes");
    }
    /**
     *  Returns ``true`` and provides a type guard is this is a [[TypedString]].
     */
    isString() {
        return (this.type === "string");
    }
    /**
     *  Returns the tuple name, if this is a tuple. Throws otherwise.
     */
    get tupleName() {
        if (this.type !== "tuple") {
            throw TypeError("not a tuple");
        }
        return this.#options;
    }
    // Returns the length of this type as an array
    // - `null` indicates the length is unforced, it could be dynamic
    // - `-1` indicates the length is dynamic
    // - any other value indicates it is a static array and is its length
    /**
     *  Returns the length of the array type or ``-1`` if it is dynamic.
     *
     *  Throws if the type is not an array.
     */
    get arrayLength() {
        if (this.type !== "array") {
            throw TypeError("not an array");
        }
        if (this.#options === true) {
            return -1;
        }
        if (this.#options === false) {
            return (this.value).length;
        }
        return null;
    }
    /**
     *  Returns a new **Typed** of %%type%% with the %%value%%.
     */
    static from(type, value) {
        return new Typed(_gaurd, type, value);
    }
    /**
     *  Return a new ``uint8`` type for %%v%%.
     */
    static uint8(v) { return n(v, 8); }
    /**
     *  Return a new ``uint16`` type for %%v%%.
     */
    static uint16(v) { return n(v, 16); }
    /**
     *  Return a new ``uint24`` type for %%v%%.
     */
    static uint24(v) { return n(v, 24); }
    /**
     *  Return a new ``uint32`` type for %%v%%.
     */
    static uint32(v) { return n(v, 32); }
    /**
     *  Return a new ``uint40`` type for %%v%%.
     */
    static uint40(v) { return n(v, 40); }
    /**
     *  Return a new ``uint48`` type for %%v%%.
     */
    static uint48(v) { return n(v, 48); }
    /**
     *  Return a new ``uint56`` type for %%v%%.
     */
    static uint56(v) { return n(v, 56); }
    /**
     *  Return a new ``uint64`` type for %%v%%.
     */
    static uint64(v) { return n(v, 64); }
    /**
     *  Return a new ``uint72`` type for %%v%%.
     */
    static uint72(v) { return n(v, 72); }
    /**
     *  Return a new ``uint80`` type for %%v%%.
     */
    static uint80(v) { return n(v, 80); }
    /**
     *  Return a new ``uint88`` type for %%v%%.
     */
    static uint88(v) { return n(v, 88); }
    /**
     *  Return a new ``uint96`` type for %%v%%.
     */
    static uint96(v) { return n(v, 96); }
    /**
     *  Return a new ``uint104`` type for %%v%%.
     */
    static uint104(v) { return n(v, 104); }
    /**
     *  Return a new ``uint112`` type for %%v%%.
     */
    static uint112(v) { return n(v, 112); }
    /**
     *  Return a new ``uint120`` type for %%v%%.
     */
    static uint120(v) { return n(v, 120); }
    /**
     *  Return a new ``uint128`` type for %%v%%.
     */
    static uint128(v) { return n(v, 128); }
    /**
     *  Return a new ``uint136`` type for %%v%%.
     */
    static uint136(v) { return n(v, 136); }
    /**
     *  Return a new ``uint144`` type for %%v%%.
     */
    static uint144(v) { return n(v, 144); }
    /**
     *  Return a new ``uint152`` type for %%v%%.
     */
    static uint152(v) { return n(v, 152); }
    /**
     *  Return a new ``uint160`` type for %%v%%.
     */
    static uint160(v) { return n(v, 160); }
    /**
     *  Return a new ``uint168`` type for %%v%%.
     */
    static uint168(v) { return n(v, 168); }
    /**
     *  Return a new ``uint176`` type for %%v%%.
     */
    static uint176(v) { return n(v, 176); }
    /**
     *  Return a new ``uint184`` type for %%v%%.
     */
    static uint184(v) { return n(v, 184); }
    /**
     *  Return a new ``uint192`` type for %%v%%.
     */
    static uint192(v) { return n(v, 192); }
    /**
     *  Return a new ``uint200`` type for %%v%%.
     */
    static uint200(v) { return n(v, 200); }
    /**
     *  Return a new ``uint208`` type for %%v%%.
     */
    static uint208(v) { return n(v, 208); }
    /**
     *  Return a new ``uint216`` type for %%v%%.
     */
    static uint216(v) { return n(v, 216); }
    /**
     *  Return a new ``uint224`` type for %%v%%.
     */
    static uint224(v) { return n(v, 224); }
    /**
     *  Return a new ``uint232`` type for %%v%%.
     */
    static uint232(v) { return n(v, 232); }
    /**
     *  Return a new ``uint240`` type for %%v%%.
     */
    static uint240(v) { return n(v, 240); }
    /**
     *  Return a new ``uint248`` type for %%v%%.
     */
    static uint248(v) { return n(v, 248); }
    /**
     *  Return a new ``uint256`` type for %%v%%.
     */
    static uint256(v) { return n(v, 256); }
    /**
     *  Return a new ``uint256`` type for %%v%%.
     */
    static uint(v) { return n(v, 256); }
    /**
     *  Return a new ``int8`` type for %%v%%.
     */
    static int8(v) { return n(v, -8); }
    /**
     *  Return a new ``int16`` type for %%v%%.
     */
    static int16(v) { return n(v, -16); }
    /**
     *  Return a new ``int24`` type for %%v%%.
     */
    static int24(v) { return n(v, -24); }
    /**
     *  Return a new ``int32`` type for %%v%%.
     */
    static int32(v) { return n(v, -32); }
    /**
     *  Return a new ``int40`` type for %%v%%.
     */
    static int40(v) { return n(v, -40); }
    /**
     *  Return a new ``int48`` type for %%v%%.
     */
    static int48(v) { return n(v, -48); }
    /**
     *  Return a new ``int56`` type for %%v%%.
     */
    static int56(v) { return n(v, -56); }
    /**
     *  Return a new ``int64`` type for %%v%%.
     */
    static int64(v) { return n(v, -64); }
    /**
     *  Return a new ``int72`` type for %%v%%.
     */
    static int72(v) { return n(v, -72); }
    /**
     *  Return a new ``int80`` type for %%v%%.
     */
    static int80(v) { return n(v, -80); }
    /**
     *  Return a new ``int88`` type for %%v%%.
     */
    static int88(v) { return n(v, -88); }
    /**
     *  Return a new ``int96`` type for %%v%%.
     */
    static int96(v) { return n(v, -96); }
    /**
     *  Return a new ``int104`` type for %%v%%.
     */
    static int104(v) { return n(v, -104); }
    /**
     *  Return a new ``int112`` type for %%v%%.
     */
    static int112(v) { return n(v, -112); }
    /**
     *  Return a new ``int120`` type for %%v%%.
     */
    static int120(v) { return n(v, -120); }
    /**
     *  Return a new ``int128`` type for %%v%%.
     */
    static int128(v) { return n(v, -128); }
    /**
     *  Return a new ``int136`` type for %%v%%.
     */
    static int136(v) { return n(v, -136); }
    /**
     *  Return a new ``int144`` type for %%v%%.
     */
    static int144(v) { return n(v, -144); }
    /**
     *  Return a new ``int52`` type for %%v%%.
     */
    static int152(v) { return n(v, -152); }
    /**
     *  Return a new ``int160`` type for %%v%%.
     */
    static int160(v) { return n(v, -160); }
    /**
     *  Return a new ``int168`` type for %%v%%.
     */
    static int168(v) { return n(v, -168); }
    /**
     *  Return a new ``int176`` type for %%v%%.
     */
    static int176(v) { return n(v, -176); }
    /**
     *  Return a new ``int184`` type for %%v%%.
     */
    static int184(v) { return n(v, -184); }
    /**
     *  Return a new ``int92`` type for %%v%%.
     */
    static int192(v) { return n(v, -192); }
    /**
     *  Return a new ``int200`` type for %%v%%.
     */
    static int200(v) { return n(v, -200); }
    /**
     *  Return a new ``int208`` type for %%v%%.
     */
    static int208(v) { return n(v, -208); }
    /**
     *  Return a new ``int216`` type for %%v%%.
     */
    static int216(v) { return n(v, -216); }
    /**
     *  Return a new ``int224`` type for %%v%%.
     */
    static int224(v) { return n(v, -224); }
    /**
     *  Return a new ``int232`` type for %%v%%.
     */
    static int232(v) { return n(v, -232); }
    /**
     *  Return a new ``int240`` type for %%v%%.
     */
    static int240(v) { return n(v, -240); }
    /**
     *  Return a new ``int248`` type for %%v%%.
     */
    static int248(v) { return n(v, -248); }
    /**
     *  Return a new ``int256`` type for %%v%%.
     */
    static int256(v) { return n(v, -256); }
    /**
     *  Return a new ``int256`` type for %%v%%.
     */
    static int(v) { return n(v, -256); }
    /**
     *  Return a new ``bytes1`` type for %%v%%.
     */
    static bytes1(v) { return b(v, 1); }
    /**
     *  Return a new ``bytes2`` type for %%v%%.
     */
    static bytes2(v) { return b(v, 2); }
    /**
     *  Return a new ``bytes3`` type for %%v%%.
     */
    static bytes3(v) { return b(v, 3); }
    /**
     *  Return a new ``bytes4`` type for %%v%%.
     */
    static bytes4(v) { return b(v, 4); }
    /**
     *  Return a new ``bytes5`` type for %%v%%.
     */
    static bytes5(v) { return b(v, 5); }
    /**
     *  Return a new ``bytes6`` type for %%v%%.
     */
    static bytes6(v) { return b(v, 6); }
    /**
     *  Return a new ``bytes7`` type for %%v%%.
     */
    static bytes7(v) { return b(v, 7); }
    /**
     *  Return a new ``bytes8`` type for %%v%%.
     */
    static bytes8(v) { return b(v, 8); }
    /**
     *  Return a new ``bytes9`` type for %%v%%.
     */
    static bytes9(v) { return b(v, 9); }
    /**
     *  Return a new ``bytes10`` type for %%v%%.
     */
    static bytes10(v) { return b(v, 10); }
    /**
     *  Return a new ``bytes11`` type for %%v%%.
     */
    static bytes11(v) { return b(v, 11); }
    /**
     *  Return a new ``bytes12`` type for %%v%%.
     */
    static bytes12(v) { return b(v, 12); }
    /**
     *  Return a new ``bytes13`` type for %%v%%.
     */
    static bytes13(v) { return b(v, 13); }
    /**
     *  Return a new ``bytes14`` type for %%v%%.
     */
    static bytes14(v) { return b(v, 14); }
    /**
     *  Return a new ``bytes15`` type for %%v%%.
     */
    static bytes15(v) { return b(v, 15); }
    /**
     *  Return a new ``bytes16`` type for %%v%%.
     */
    static bytes16(v) { return b(v, 16); }
    /**
     *  Return a new ``bytes17`` type for %%v%%.
     */
    static bytes17(v) { return b(v, 17); }
    /**
     *  Return a new ``bytes18`` type for %%v%%.
     */
    static bytes18(v) { return b(v, 18); }
    /**
     *  Return a new ``bytes19`` type for %%v%%.
     */
    static bytes19(v) { return b(v, 19); }
    /**
     *  Return a new ``bytes20`` type for %%v%%.
     */
    static bytes20(v) { return b(v, 20); }
    /**
     *  Return a new ``bytes21`` type for %%v%%.
     */
    static bytes21(v) { return b(v, 21); }
    /**
     *  Return a new ``bytes22`` type for %%v%%.
     */
    static bytes22(v) { return b(v, 22); }
    /**
     *  Return a new ``bytes23`` type for %%v%%.
     */
    static bytes23(v) { return b(v, 23); }
    /**
     *  Return a new ``bytes24`` type for %%v%%.
     */
    static bytes24(v) { return b(v, 24); }
    /**
     *  Return a new ``bytes25`` type for %%v%%.
     */
    static bytes25(v) { return b(v, 25); }
    /**
     *  Return a new ``bytes26`` type for %%v%%.
     */
    static bytes26(v) { return b(v, 26); }
    /**
     *  Return a new ``bytes27`` type for %%v%%.
     */
    static bytes27(v) { return b(v, 27); }
    /**
     *  Return a new ``bytes28`` type for %%v%%.
     */
    static bytes28(v) { return b(v, 28); }
    /**
     *  Return a new ``bytes29`` type for %%v%%.
     */
    static bytes29(v) { return b(v, 29); }
    /**
     *  Return a new ``bytes30`` type for %%v%%.
     */
    static bytes30(v) { return b(v, 30); }
    /**
     *  Return a new ``bytes31`` type for %%v%%.
     */
    static bytes31(v) { return b(v, 31); }
    /**
     *  Return a new ``bytes32`` type for %%v%%.
     */
    static bytes32(v) { return b(v, 32); }
    /**
     *  Return a new ``address`` type for %%v%%.
     */
    static address(v) { return new Typed(_gaurd, "address", v); }
    /**
     *  Return a new ``bool`` type for %%v%%.
     */
    static bool(v) { return new Typed(_gaurd, "bool", !!v); }
    /**
     *  Return a new ``bytes`` type for %%v%%.
     */
    static bytes(v) { return new Typed(_gaurd, "bytes", v); }
    /**
     *  Return a new ``string`` type for %%v%%.
     */
    static string(v) { return new Typed(_gaurd, "string", v); }
    /**
     *  Return a new ``array`` type for %%v%%, allowing %%dynamic%% length.
     */
    static array(v, dynamic) {
        throw new Error("not implemented yet");
        return new Typed(_gaurd, "array", v, dynamic);
    }
    /**
     *  Return a new ``tuple`` type for %%v%%, with the optional %%name%%.
     */
    static tuple(v, name) {
        throw new Error("not implemented yet");
        return new Typed(_gaurd, "tuple", v, name);
    }
    /**
     *  Return a new ``uint8`` type for %%v%%.
     */
    static overrides(v) {
        return new Typed(_gaurd, "overrides", Object.assign({}, v));
    }
    /**
     *  Returns true only if %%value%% is a [[Typed]] instance.
     */
    static isTyped(value) {
        return (value
            && typeof (value) === "object"
            && "_typedSymbol" in value
            && value._typedSymbol === _typedSymbol);
    }
    /**
     *  If the value is a [[Typed]] instance, validates the underlying value
     *  and returns it, otherwise returns value directly.
     *
     *  This is useful for functions that with to accept either a [[Typed]]
     *  object or values.
     */
    static dereference(value, type) {
        if (Typed.isTyped(value)) {
            if (value.type !== type) {
                throw new Error(`invalid type: expecetd ${type}, got ${value.type}`);
            }
            return value.value;
        }
        return value;
    }
}
exports.Typed = Typed;
//# sourceMappingURL=typed.js.map