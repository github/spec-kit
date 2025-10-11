"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AnonymousCoder = void 0;
const abstract_coder_js_1 = require("./abstract-coder.js");
/**
 *  Clones the functionality of an existing Coder, but without a localName
 *
 *  @_ignore
 */
class AnonymousCoder extends abstract_coder_js_1.Coder {
    coder;
    constructor(coder) {
        super(coder.name, coder.type, "_", coder.dynamic);
        this.coder = coder;
    }
    defaultValue() {
        return this.coder.defaultValue();
    }
    encode(writer, value) {
        return this.coder.encode(writer, value);
    }
    decode(reader) {
        return this.coder.decode(reader);
    }
}
exports.AnonymousCoder = AnonymousCoder;
//# sourceMappingURL=anonymous.js.map