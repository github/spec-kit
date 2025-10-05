import { defineProperties, fromTwos, getBigInt, mask, toTwos } from "../../utils/index.js";
import { Typed } from "../typed.js";
import { Coder, WordSize } from "./abstract-coder.js";
const BN_0 = BigInt(0);
const BN_1 = BigInt(1);
const BN_MAX_UINT256 = BigInt("0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff");
/**
 *  @_ignore
 */
export class NumberCoder extends Coder {
    size;
    signed;
    constructor(size, signed, localName) {
        const name = ((signed ? "int" : "uint") + (size * 8));
        super(name, name, localName, false);
        defineProperties(this, { size, signed }, { size: "number", signed: "boolean" });
    }
    defaultValue() {
        return 0;
    }
    encode(writer, _value) {
        let value = getBigInt(Typed.dereference(_value, this.type));
        // Check bounds are safe for encoding
        let maxUintValue = mask(BN_MAX_UINT256, WordSize * 8);
        if (this.signed) {
            let bounds = mask(maxUintValue, (this.size * 8) - 1);
            if (value > bounds || value < -(bounds + BN_1)) {
                this._throwError("value out-of-bounds", _value);
            }
            value = toTwos(value, 8 * WordSize);
        }
        else if (value < BN_0 || value > mask(maxUintValue, this.size * 8)) {
            this._throwError("value out-of-bounds", _value);
        }
        return writer.writeValue(value);
    }
    decode(reader) {
        let value = mask(reader.readValue(), this.size * 8);
        if (this.signed) {
            value = fromTwos(value, this.size * 8);
        }
        return value;
    }
}
//# sourceMappingURL=number.js.map