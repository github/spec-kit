"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.NumberCoder = void 0;
const index_js_1 = require("../../utils/index.js");
const typed_js_1 = require("../typed.js");
const abstract_coder_js_1 = require("./abstract-coder.js");
const BN_0 = BigInt(0);
const BN_1 = BigInt(1);
const BN_MAX_UINT256 = BigInt("0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff");
/**
 *  @_ignore
 */
class NumberCoder extends abstract_coder_js_1.Coder {
    size;
    signed;
    constructor(size, signed, localName) {
        const name = ((signed ? "int" : "uint") + (size * 8));
        super(name, name, localName, false);
        (0, index_js_1.defineProperties)(this, { size, signed }, { size: "number", signed: "boolean" });
    }
    defaultValue() {
        return 0;
    }
    encode(writer, _value) {
        let value = (0, index_js_1.getBigInt)(typed_js_1.Typed.dereference(_value, this.type));
        // Check bounds are safe for encoding
        let maxUintValue = (0, index_js_1.mask)(BN_MAX_UINT256, abstract_coder_js_1.WordSize * 8);
        if (this.signed) {
            let bounds = (0, index_js_1.mask)(maxUintValue, (this.size * 8) - 1);
            if (value > bounds || value < -(bounds + BN_1)) {
                this._throwError("value out-of-bounds", _value);
            }
            value = (0, index_js_1.toTwos)(value, 8 * abstract_coder_js_1.WordSize);
        }
        else if (value < BN_0 || value > (0, index_js_1.mask)(maxUintValue, this.size * 8)) {
            this._throwError("value out-of-bounds", _value);
        }
        return writer.writeValue(value);
    }
    decode(reader) {
        let value = (0, index_js_1.mask)(reader.readValue(), this.size * 8);
        if (this.signed) {
            value = (0, index_js_1.fromTwos)(value, this.size * 8);
        }
        return value;
    }
}
exports.NumberCoder = NumberCoder;
//# sourceMappingURL=number.js.map