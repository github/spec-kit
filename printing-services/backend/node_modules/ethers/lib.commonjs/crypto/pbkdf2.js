"use strict";
/**
 *  A **Password-Based Key-Derivation Function** is designed to create
 *  a sequence of bytes suitible as a **key** from a human-rememberable
 *  password.
 *
 *  @_subsection: api/crypto:Passwords  [about-pbkdf]
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.pbkdf2 = void 0;
const crypto_js_1 = require("./crypto.js");
const index_js_1 = require("../utils/index.js");
let locked = false;
const _pbkdf2 = function (password, salt, iterations, keylen, algo) {
    return (0, crypto_js_1.pbkdf2Sync)(password, salt, iterations, keylen, algo);
};
let __pbkdf2 = _pbkdf2;
/**
 *  Return the [[link-pbkdf2]] for %%keylen%% bytes for %%password%% using
 *  the %%salt%% and using %%iterations%% of %%algo%%.
 *
 *  This PBKDF is outdated and should not be used in new projects, but is
 *  required to decrypt older files.
 *
 *  @example:
 *    // The password must be converted to bytes, and it is generally
 *    // best practices to ensure the string has been normalized. Many
 *    // formats explicitly indicate the normalization form to use.
 *    password = "hello"
 *    passwordBytes = toUtf8Bytes(password, "NFKC")
 *
 *    salt = id("some-salt")
 *
 *    // Compute the PBKDF2
 *    pbkdf2(passwordBytes, salt, 1024, 16, "sha256")
 *    //_result:
 */
function pbkdf2(_password, _salt, iterations, keylen, algo) {
    const password = (0, index_js_1.getBytes)(_password, "password");
    const salt = (0, index_js_1.getBytes)(_salt, "salt");
    return (0, index_js_1.hexlify)(__pbkdf2(password, salt, iterations, keylen, algo));
}
exports.pbkdf2 = pbkdf2;
pbkdf2._ = _pbkdf2;
pbkdf2.lock = function () { locked = true; };
pbkdf2.register = function (func) {
    if (locked) {
        throw new Error("pbkdf2 is locked");
    }
    __pbkdf2 = func;
};
Object.freeze(pbkdf2);
//# sourceMappingURL=pbkdf2.js.map