"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.computeHmac = void 0;
/**
 *  An **HMAC** enables verification that a given key was used
 *  to authenticate a payload.
 *
 *  See: [[link-wiki-hmac]]
 *
 *  @_subsection: api/crypto:HMAC  [about-hmac]
 */
const crypto_js_1 = require("./crypto.js");
const index_js_1 = require("../utils/index.js");
let locked = false;
const _computeHmac = function (algorithm, key, data) {
    return (0, crypto_js_1.createHmac)(algorithm, key).update(data).digest();
};
let __computeHmac = _computeHmac;
/**
 *  Return the HMAC for %%data%% using the %%key%% key with the underlying
 *  %%algo%% used for compression.
 *
 *  @example:
 *    key = id("some-secret")
 *
 *    // Compute the HMAC
 *    computeHmac("sha256", key, "0x1337")
 *    //_result:
 *
 *    // To compute the HMAC of UTF-8 data, the data must be
 *    // converted to UTF-8 bytes
 *    computeHmac("sha256", key, toUtf8Bytes("Hello World"))
 *    //_result:
 *
 */
function computeHmac(algorithm, _key, _data) {
    const key = (0, index_js_1.getBytes)(_key, "key");
    const data = (0, index_js_1.getBytes)(_data, "data");
    return (0, index_js_1.hexlify)(__computeHmac(algorithm, key, data));
}
exports.computeHmac = computeHmac;
computeHmac._ = _computeHmac;
computeHmac.lock = function () { locked = true; };
computeHmac.register = function (func) {
    if (locked) {
        throw new Error("computeHmac is locked");
    }
    __computeHmac = func;
};
Object.freeze(computeHmac);
//# sourceMappingURL=hmac.js.map