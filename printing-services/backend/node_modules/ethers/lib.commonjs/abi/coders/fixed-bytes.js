"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FixedBytesCoder = void 0;
const index_js_1 = require("../../utils/index.js");
const typed_js_1 = require("../typed.js");
const abstract_coder_js_1 = require("./abstract-coder.js");
/**
 *  @_ignore
 */
class FixedBytesCoder extends abstract_coder_js_1.Coder {
    size;
    constructor(size, localName) {
        let name = "bytes" + String(size);
        super(name, name, localName, false);
        (0, index_js_1.defineProperties)(this, { size }, { size: "number" });
    }
    defaultValue() {
        return ("0x0000000000000000000000000000000000000000000000000000000000000000").substring(0, 2 + this.size * 2);
    }
    encode(writer, _value) {
        let data = (0, index_js_1.getBytesCopy)(typed_js_1.Typed.dereference(_value, this.type));
        if (data.length !== this.size) {
            this._throwError("incorrect data length", _value);
        }
        return writer.writeBytes(data);
    }
    decode(reader) {
        return (0, index_js_1.hexlify)(reader.readBytes(this.size));
    }
}
exports.FixedBytesCoder = FixedBytesCoder;
//# sourceMappingURL=fixed-bytes.js.map