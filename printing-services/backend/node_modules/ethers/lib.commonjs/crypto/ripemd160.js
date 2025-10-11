"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ripemd160 = void 0;
const ripemd160_1 = require("@noble/hashes/ripemd160");
const index_js_1 = require("../utils/index.js");
let locked = false;
const _ripemd160 = function (data) {
    return (0, ripemd160_1.ripemd160)(data);
};
let __ripemd160 = _ripemd160;
/**
 *  Compute the cryptographic RIPEMD-160 hash of %%data%%.
 *
 *  @_docloc: api/crypto:Hash Functions
 *  @returns DataHexstring
 *
 *  @example:
 *    ripemd160("0x")
 *    //_result:
 *
 *    ripemd160("0x1337")
 *    //_result:
 *
 *    ripemd160(new Uint8Array([ 0x13, 0x37 ]))
 *    //_result:
 *
 */
function ripemd160(_data) {
    const data = (0, index_js_1.getBytes)(_data, "data");
    return (0, index_js_1.hexlify)(__ripemd160(data));
}
exports.ripemd160 = ripemd160;
ripemd160._ = _ripemd160;
ripemd160.lock = function () { locked = true; };
ripemd160.register = function (func) {
    if (locked) {
        throw new TypeError("ripemd160 is locked");
    }
    __ripemd160 = func;
};
Object.freeze(ripemd160);
//# sourceMappingURL=ripemd160.js.map