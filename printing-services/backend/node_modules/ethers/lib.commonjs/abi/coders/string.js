"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.StringCoder = void 0;
const utf8_js_1 = require("../../utils/utf8.js");
const typed_js_1 = require("../typed.js");
const bytes_js_1 = require("./bytes.js");
/**
 *  @_ignore
 */
class StringCoder extends bytes_js_1.DynamicBytesCoder {
    constructor(localName) {
        super("string", localName);
    }
    defaultValue() {
        return "";
    }
    encode(writer, _value) {
        return super.encode(writer, (0, utf8_js_1.toUtf8Bytes)(typed_js_1.Typed.dereference(_value, "string")));
    }
    decode(reader) {
        return (0, utf8_js_1.toUtf8String)(super.decode(reader));
    }
}
exports.StringCoder = StringCoder;
//# sourceMappingURL=string.js.map