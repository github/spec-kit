"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.decodeOwlA = void 0;
const index_js_1 = require("../utils/index.js");
const bit_reader_js_1 = require("./bit-reader.js");
const decode_owl_js_1 = require("./decode-owl.js");
/**
 *  @_ignore
 */
function decodeOwlA(data, accents) {
    let words = (0, decode_owl_js_1.decodeOwl)(data).join(",");
    // Inject the accents
    accents.split(/,/g).forEach((accent) => {
        const match = accent.match(/^([a-z]*)([0-9]+)([0-9])(.*)$/);
        (0, index_js_1.assertArgument)(match !== null, "internal error parsing accents", "accents", accents);
        let posOffset = 0;
        const positions = (0, bit_reader_js_1.decodeBits)(parseInt(match[3]), match[4]);
        const charCode = parseInt(match[2]);
        const regex = new RegExp(`([${match[1]}])`, "g");
        words = words.replace(regex, (all, letter) => {
            const rem = --positions[posOffset];
            if (rem === 0) {
                letter = String.fromCharCode(letter.charCodeAt(0), charCode);
                posOffset++;
            }
            return letter;
        });
    });
    return words.split(",");
}
exports.decodeOwlA = decodeOwlA;
//# sourceMappingURL=decode-owla.js.map