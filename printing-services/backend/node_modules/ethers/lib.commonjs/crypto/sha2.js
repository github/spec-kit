"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.sha512 = exports.sha256 = void 0;
const crypto_js_1 = require("./crypto.js");
const index_js_1 = require("../utils/index.js");
const _sha256 = function (data) {
    return (0, crypto_js_1.createHash)("sha256").update(data).digest();
};
const _sha512 = function (data) {
    return (0, crypto_js_1.createHash)("sha512").update(data).digest();
};
let __sha256 = _sha256;
let __sha512 = _sha512;
let locked256 = false, locked512 = false;
/**
 *  Compute the cryptographic SHA2-256 hash of %%data%%.
 *
 *  @_docloc: api/crypto:Hash Functions
 *  @returns DataHexstring
 *
 *  @example:
 *    sha256("0x")
 *    //_result:
 *
 *    sha256("0x1337")
 *    //_result:
 *
 *    sha256(new Uint8Array([ 0x13, 0x37 ]))
 *    //_result:
 *
 */
function sha256(_data) {
    const data = (0, index_js_1.getBytes)(_data, "data");
    return (0, index_js_1.hexlify)(__sha256(data));
}
exports.sha256 = sha256;
sha256._ = _sha256;
sha256.lock = function () { locked256 = true; };
sha256.register = function (func) {
    if (locked256) {
        throw new Error("sha256 is locked");
    }
    __sha256 = func;
};
Object.freeze(sha256);
/**
 *  Compute the cryptographic SHA2-512 hash of %%data%%.
 *
 *  @_docloc: api/crypto:Hash Functions
 *  @returns DataHexstring
 *
 *  @example:
 *    sha512("0x")
 *    //_result:
 *
 *    sha512("0x1337")
 *    //_result:
 *
 *    sha512(new Uint8Array([ 0x13, 0x37 ]))
 *    //_result:
 */
function sha512(_data) {
    const data = (0, index_js_1.getBytes)(_data, "data");
    return (0, index_js_1.hexlify)(__sha512(data));
}
exports.sha512 = sha512;
sha512._ = _sha512;
sha512.lock = function () { locked512 = true; };
sha512.register = function (func) {
    if (locked512) {
        throw new Error("sha512 is locked");
    }
    __sha512 = func;
};
Object.freeze(sha256);
//# sourceMappingURL=sha2.js.map