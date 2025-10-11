"use strict";
/**
 *  A fundamental building block of Ethereum is the underlying
 *  cryptographic primitives.
 *
 *  @_section: api/crypto:Cryptographic Functions   [about-crypto]
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.lock = exports.Signature = exports.SigningKey = exports.scryptSync = exports.scrypt = exports.pbkdf2 = exports.sha512 = exports.sha256 = exports.ripemd160 = exports.keccak256 = exports.randomBytes = exports.computeHmac = void 0;
null;
// We import all these so we can export lock()
const hmac_js_1 = require("./hmac.js");
Object.defineProperty(exports, "computeHmac", { enumerable: true, get: function () { return hmac_js_1.computeHmac; } });
const keccak_js_1 = require("./keccak.js");
Object.defineProperty(exports, "keccak256", { enumerable: true, get: function () { return keccak_js_1.keccak256; } });
const ripemd160_js_1 = require("./ripemd160.js");
Object.defineProperty(exports, "ripemd160", { enumerable: true, get: function () { return ripemd160_js_1.ripemd160; } });
const pbkdf2_js_1 = require("./pbkdf2.js");
Object.defineProperty(exports, "pbkdf2", { enumerable: true, get: function () { return pbkdf2_js_1.pbkdf2; } });
const random_js_1 = require("./random.js");
Object.defineProperty(exports, "randomBytes", { enumerable: true, get: function () { return random_js_1.randomBytes; } });
const scrypt_js_1 = require("./scrypt.js");
Object.defineProperty(exports, "scrypt", { enumerable: true, get: function () { return scrypt_js_1.scrypt; } });
Object.defineProperty(exports, "scryptSync", { enumerable: true, get: function () { return scrypt_js_1.scryptSync; } });
const sha2_js_1 = require("./sha2.js");
Object.defineProperty(exports, "sha256", { enumerable: true, get: function () { return sha2_js_1.sha256; } });
Object.defineProperty(exports, "sha512", { enumerable: true, get: function () { return sha2_js_1.sha512; } });
var signing_key_js_1 = require("./signing-key.js");
Object.defineProperty(exports, "SigningKey", { enumerable: true, get: function () { return signing_key_js_1.SigningKey; } });
var signature_js_1 = require("./signature.js");
Object.defineProperty(exports, "Signature", { enumerable: true, get: function () { return signature_js_1.Signature; } });
/**
 *  Once called, prevents any future change to the underlying cryptographic
 *  primitives using the ``.register`` feature for hooks.
 */
function lock() {
    hmac_js_1.computeHmac.lock();
    keccak_js_1.keccak256.lock();
    pbkdf2_js_1.pbkdf2.lock();
    random_js_1.randomBytes.lock();
    ripemd160_js_1.ripemd160.lock();
    scrypt_js_1.scrypt.lock();
    scrypt_js_1.scryptSync.lock();
    sha2_js_1.sha256.lock();
    sha2_js_1.sha512.lock();
    random_js_1.randomBytes.lock();
}
exports.lock = lock;
//# sourceMappingURL=index.js.map