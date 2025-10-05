"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.scryptSync = exports.scrypt = void 0;
const scrypt_1 = require("@noble/hashes/scrypt");
const index_js_1 = require("../utils/index.js");
let lockedSync = false, lockedAsync = false;
const _scryptAsync = async function (passwd, salt, N, r, p, dkLen, onProgress) {
    return await (0, scrypt_1.scryptAsync)(passwd, salt, { N, r, p, dkLen, onProgress });
};
const _scryptSync = function (passwd, salt, N, r, p, dkLen) {
    return (0, scrypt_1.scrypt)(passwd, salt, { N, r, p, dkLen });
};
let __scryptAsync = _scryptAsync;
let __scryptSync = _scryptSync;
/**
 *  The [[link-wiki-scrypt]] uses a memory and cpu hard method of
 *  derivation to increase the resource cost to brute-force a password
 *  for a given key.
 *
 *  This means this algorithm is intentionally slow, and can be tuned to
 *  become slower. As computation and memory speed improve over time,
 *  increasing the difficulty maintains the cost of an attacker.
 *
 *  For example, if a target time of 5 seconds is used, a legitimate user
 *  which knows their password requires only 5 seconds to unlock their
 *  account. A 6 character password has 68 billion possibilities, which
 *  would require an attacker to invest over 10,000 years of CPU time. This
 *  is of course a crude example (as password generally aren't random),
 *  but demonstrates to value of imposing large costs to decryption.
 *
 *  For this reason, if building a UI which involved decrypting or
 *  encrypting datsa using scrypt, it is recommended to use a
 *  [[ProgressCallback]] (as event short periods can seem lik an eternity
 *  if the UI freezes). Including the phrase //"decrypting"// in the UI
 *  can also help, assuring the user their waiting is for a good reason.
 *
 *  @_docloc: api/crypto:Passwords
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
 *    // Compute the scrypt
 *    scrypt(passwordBytes, salt, 1024, 8, 1, 16)
 *    //_result:
 */
async function scrypt(_passwd, _salt, N, r, p, dkLen, progress) {
    const passwd = (0, index_js_1.getBytes)(_passwd, "passwd");
    const salt = (0, index_js_1.getBytes)(_salt, "salt");
    return (0, index_js_1.hexlify)(await __scryptAsync(passwd, salt, N, r, p, dkLen, progress));
}
exports.scrypt = scrypt;
scrypt._ = _scryptAsync;
scrypt.lock = function () { lockedAsync = true; };
scrypt.register = function (func) {
    if (lockedAsync) {
        throw new Error("scrypt is locked");
    }
    __scryptAsync = func;
};
Object.freeze(scrypt);
/**
 *  Provides a synchronous variant of [[scrypt]].
 *
 *  This will completely lock up and freeze the UI in a browser and will
 *  prevent any event loop from progressing. For this reason, it is
 *  preferred to use the [async variant](scrypt).
 *
 *  @_docloc: api/crypto:Passwords
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
 *    // Compute the scrypt
 *    scryptSync(passwordBytes, salt, 1024, 8, 1, 16)
 *    //_result:
 */
function scryptSync(_passwd, _salt, N, r, p, dkLen) {
    const passwd = (0, index_js_1.getBytes)(_passwd, "passwd");
    const salt = (0, index_js_1.getBytes)(_salt, "salt");
    return (0, index_js_1.hexlify)(__scryptSync(passwd, salt, N, r, p, dkLen));
}
exports.scryptSync = scryptSync;
scryptSync._ = _scryptSync;
scryptSync.lock = function () { lockedSync = true; };
scryptSync.register = function (func) {
    if (lockedSync) {
        throw new Error("scryptSync is locked");
    }
    __scryptSync = func;
};
Object.freeze(scryptSync);
//# sourceMappingURL=scrypt.js.map