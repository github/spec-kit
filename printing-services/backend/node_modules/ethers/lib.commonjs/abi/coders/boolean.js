"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BooleanCoder = void 0;
const typed_js_1 = require("../typed.js");
const abstract_coder_js_1 = require("./abstract-coder.js");
/**
 *  @_ignore
 */
class BooleanCoder extends abstract_coder_js_1.Coder {
    constructor(localName) {
        super("bool", "bool", localName, false);
    }
    defaultValue() {
        return false;
    }
    encode(writer, _value) {
        const value = typed_js_1.Typed.dereference(_value, "bool");
        return writer.writeValue(value ? 1 : 0);
    }
    decode(reader) {
        return !!reader.readValue();
    }
}
exports.BooleanCoder = BooleanCoder;
//# sourceMappingURL=boolean.js.map