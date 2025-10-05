"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BytesCoder = exports.DynamicBytesCoder = void 0;
const index_js_1 = require("../../utils/index.js");
const abstract_coder_js_1 = require("./abstract-coder.js");
/**
 *  @_ignore
 */
class DynamicBytesCoder extends abstract_coder_js_1.Coder {
    constructor(type, localName) {
        super(type, type, localName, true);
    }
    defaultValue() {
        return "0x";
    }
    encode(writer, value) {
        value = (0, index_js_1.getBytesCopy)(value);
        let length = writer.writeValue(value.length);
        length += writer.writeBytes(value);
        return length;
    }
    decode(reader) {
        return reader.readBytes(reader.readIndex(), true);
    }
}
exports.DynamicBytesCoder = DynamicBytesCoder;
/**
 *  @_ignore
 */
class BytesCoder extends DynamicBytesCoder {
    constructor(localName) {
        super("bytes", localName);
    }
    decode(reader) {
        return (0, index_js_1.hexlify)(super.decode(reader));
    }
}
exports.BytesCoder = BytesCoder;
//# sourceMappingURL=bytes.js.map