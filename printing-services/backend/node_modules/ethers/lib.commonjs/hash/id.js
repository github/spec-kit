"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.id = void 0;
const index_js_1 = require("../crypto/index.js");
const index_js_2 = require("../utils/index.js");
/**
 *  A simple hashing function which operates on UTF-8 strings to
 *  compute an 32-byte identifier.
 *
 *  This simply computes the [UTF-8 bytes](toUtf8Bytes) and computes
 *  the [[keccak256]].
 *
 *  @example:
 *    id("hello world")
 *    //_result:
 */
function id(value) {
    return (0, index_js_1.keccak256)((0, index_js_2.toUtf8Bytes)(value));
}
exports.id = id;
//# sourceMappingURL=id.js.map