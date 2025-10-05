"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AddressCoder = void 0;
const index_js_1 = require("../../address/index.js");
const maths_js_1 = require("../../utils/maths.js");
const typed_js_1 = require("../typed.js");
const abstract_coder_js_1 = require("./abstract-coder.js");
/**
 *  @_ignore
 */
class AddressCoder extends abstract_coder_js_1.Coder {
    constructor(localName) {
        super("address", "address", localName, false);
    }
    defaultValue() {
        return "0x0000000000000000000000000000000000000000";
    }
    encode(writer, _value) {
        let value = typed_js_1.Typed.dereference(_value, "string");
        try {
            value = (0, index_js_1.getAddress)(value);
        }
        catch (error) {
            return this._throwError(error.message, _value);
        }
        return writer.writeValue(value);
    }
    decode(reader) {
        return (0, index_js_1.getAddress)((0, maths_js_1.toBeHex)(reader.readValue(), 20));
    }
}
exports.AddressCoder = AddressCoder;
//# sourceMappingURL=address.js.map