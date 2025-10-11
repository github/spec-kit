"use strict";
/**
 *  Cryptographic hashing functions
 *
 *  @_subsection: api/crypto:Hash Functions [about-crypto-hashing]
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.keccak256 = void 0;
const sha3_1 = require("@noble/hashes/sha3");
const index_js_1 = require("../utils/index.js");
let locked = false;
const _keccak256 = function (data) {
    return (0, sha3_1.keccak_256)(data);
};
let __keccak256 = _keccak256;
/**
 *  Compute the cryptographic KECCAK256 hash of %%data%%.
 *
 *  The %%data%% **must** be a data representation, to compute the
 *  hash of UTF-8 data use the [[id]] function.
 *
 *  @returns DataHexstring
 *  @example:
 *    keccak256("0x")
 *    //_result:
 *
 *    keccak256("0x1337")
 *    //_result:
 *
 *    keccak256(new Uint8Array([ 0x13, 0x37 ]))
 *    //_result:
 *
 *    // Strings are assumed to be DataHexString, otherwise it will
 *    // throw. To hash UTF-8 data, see the note above.
 *    keccak256("Hello World")
 *    //_error:
 */
function keccak256(_data) {
    const data = (0, index_js_1.getBytes)(_data, "data");
    return (0, index_js_1.hexlify)(__keccak256(data));
}
exports.keccak256 = keccak256;
keccak256._ = _keccak256;
keccak256.lock = function () { locked = true; };
keccak256.register = function (func) {
    if (locked) {
        throw new TypeError("keccak256 is locked");
    }
    __keccak256 = func;
};
Object.freeze(keccak256);
//# sourceMappingURL=keccak.js.map