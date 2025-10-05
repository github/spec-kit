"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TupleCoder = void 0;
const properties_js_1 = require("../../utils/properties.js");
const typed_js_1 = require("../typed.js");
const abstract_coder_js_1 = require("./abstract-coder.js");
const array_js_1 = require("./array.js");
/**
 *  @_ignore
 */
class TupleCoder extends abstract_coder_js_1.Coder {
    coders;
    constructor(coders, localName) {
        let dynamic = false;
        const types = [];
        coders.forEach((coder) => {
            if (coder.dynamic) {
                dynamic = true;
            }
            types.push(coder.type);
        });
        const type = ("tuple(" + types.join(",") + ")");
        super("tuple", type, localName, dynamic);
        (0, properties_js_1.defineProperties)(this, { coders: Object.freeze(coders.slice()) });
    }
    defaultValue() {
        const values = [];
        this.coders.forEach((coder) => {
            values.push(coder.defaultValue());
        });
        // We only output named properties for uniquely named coders
        const uniqueNames = this.coders.reduce((accum, coder) => {
            const name = coder.localName;
            if (name) {
                if (!accum[name]) {
                    accum[name] = 0;
                }
                accum[name]++;
            }
            return accum;
        }, {});
        // Add named values
        this.coders.forEach((coder, index) => {
            let name = coder.localName;
            if (!name || uniqueNames[name] !== 1) {
                return;
            }
            if (name === "length") {
                name = "_length";
            }
            if (values[name] != null) {
                return;
            }
            values[name] = values[index];
        });
        return Object.freeze(values);
    }
    encode(writer, _value) {
        const value = typed_js_1.Typed.dereference(_value, "tuple");
        return (0, array_js_1.pack)(writer, this.coders, value);
    }
    decode(reader) {
        return (0, array_js_1.unpack)(reader, this.coders);
    }
}
exports.TupleCoder = TupleCoder;
//# sourceMappingURL=tuple.js.map