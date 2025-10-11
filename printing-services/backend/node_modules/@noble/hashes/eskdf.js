"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.eskdf = exports.deriveMainSeed = exports.pbkdf2 = exports.scrypt = void 0;
const _assert_js_1 = require("./_assert.js");
const hkdf_js_1 = require("./hkdf.js");
const sha256_js_1 = require("./sha256.js");
const pbkdf2_js_1 = require("./pbkdf2.js");
const scrypt_js_1 = require("./scrypt.js");
const utils_js_1 = require("./utils.js");
// A tiny KDF for various applications like AES key-gen.
// Uses HKDF in a non-standard way, so it's not "KDF-secure", only "PRF-secure".
// Which is good enough: assume sha2-256 retained preimage resistance.
const SCRYPT_FACTOR = 2 ** 19;
const PBKDF2_FACTOR = 2 ** 17;
// Scrypt KDF
function scrypt(password, salt) {
    return (0, scrypt_js_1.scrypt)(password, salt, { N: SCRYPT_FACTOR, r: 8, p: 1, dkLen: 32 });
}
exports.scrypt = scrypt;
// PBKDF2-HMAC-SHA256
function pbkdf2(password, salt) {
    return (0, pbkdf2_js_1.pbkdf2)(sha256_js_1.sha256, password, salt, { c: PBKDF2_FACTOR, dkLen: 32 });
}
exports.pbkdf2 = pbkdf2;
// Combines two 32-byte byte arrays
function xor32(a, b) {
    (0, _assert_js_1.bytes)(a, 32);
    (0, _assert_js_1.bytes)(b, 32);
    const arr = new Uint8Array(32);
    for (let i = 0; i < 32; i++) {
        arr[i] = a[i] ^ b[i];
    }
    return arr;
}
function strHasLength(str, min, max) {
    return typeof str === 'string' && str.length >= min && str.length <= max;
}
/**
 * Derives main seed. Takes a lot of time. Prefer `eskdf` method instead.
 */
function deriveMainSeed(username, password) {
    if (!strHasLength(username, 8, 255))
        throw new Error('invalid username');
    if (!strHasLength(password, 8, 255))
        throw new Error('invalid password');
    const scr = scrypt(password + '\u{1}', username + '\u{1}');
    const pbk = pbkdf2(password + '\u{2}', username + '\u{2}');
    const res = xor32(scr, pbk);
    scr.fill(0);
    pbk.fill(0);
    return res;
}
exports.deriveMainSeed = deriveMainSeed;
/**
 * Converts protocol & accountId pair to HKDF salt & info params.
 */
function getSaltInfo(protocol, accountId = 0) {
    // Note that length here also repeats two lines below
    // We do an additional length check here to reduce the scope of DoS attacks
    if (!(strHasLength(protocol, 3, 15) && /^[a-z0-9]{3,15}$/.test(protocol))) {
        throw new Error('invalid protocol');
    }
    // Allow string account ids for some protocols
    const allowsStr = /^password\d{0,3}|ssh|tor|file$/.test(protocol);
    let salt; // Extract salt. Default is undefined.
    if (typeof accountId === 'string') {
        if (!allowsStr)
            throw new Error('accountId must be a number');
        if (!strHasLength(accountId, 1, 255))
            throw new Error('accountId must be valid string');
        salt = (0, utils_js_1.toBytes)(accountId);
    }
    else if (Number.isSafeInteger(accountId)) {
        if (accountId < 0 || accountId > 2 ** 32 - 1)
            throw new Error('invalid accountId');
        // Convert to Big Endian Uint32
        salt = new Uint8Array(4);
        (0, utils_js_1.createView)(salt).setUint32(0, accountId, false);
    }
    else {
        throw new Error(`accountId must be a number${allowsStr ? ' or string' : ''}`);
    }
    const info = (0, utils_js_1.toBytes)(protocol);
    return { salt, info };
}
function countBytes(num) {
    if (typeof num !== 'bigint' || num <= BigInt(128))
        throw new Error('invalid number');
    return Math.ceil(num.toString(2).length / 8);
}
/**
 * Parses keyLength and modulus options to extract length of result key.
 * If modulus is used, adds 64 bits to it as per FIPS 186 B.4.1 to combat modulo bias.
 */
function getKeyLength(options) {
    if (!options || typeof options !== 'object')
        return 32;
    const hasLen = 'keyLength' in options;
    const hasMod = 'modulus' in options;
    if (hasLen && hasMod)
        throw new Error('cannot combine keyLength and modulus options');
    if (!hasLen && !hasMod)
        throw new Error('must have either keyLength or modulus option');
    // FIPS 186 B.4.1 requires at least 64 more bits
    const l = hasMod ? countBytes(options.modulus) + 8 : options.keyLength;
    if (!(typeof l === 'number' && l >= 16 && l <= 8192))
        throw new Error('invalid keyLength');
    return l;
}
/**
 * Converts key to bigint and divides it by modulus. Big Endian.
 * Implements FIPS 186 B.4.1, which removes 0 and modulo bias from output.
 */
function modReduceKey(key, modulus) {
    const _1 = BigInt(1);
    const num = BigInt('0x' + (0, utils_js_1.bytesToHex)(key)); // check for ui8a, then bytesToNumber()
    const res = (num % (modulus - _1)) + _1; // Remove 0 from output
    if (res < _1)
        throw new Error('expected positive number'); // Guard against bad values
    const len = key.length - 8; // FIPS requires 64 more bits = 8 bytes
    const hex = res.toString(16).padStart(len * 2, '0'); // numberToHex()
    const bytes = (0, utils_js_1.hexToBytes)(hex);
    if (bytes.length !== len)
        throw new Error('invalid length of result key');
    return bytes;
}
/**
 * ESKDF
 * @param username - username, email, or identifier, min: 8 characters, should have enough entropy
 * @param password - password, min: 8 characters, should have enough entropy
 * @example
 * const kdf = await eskdf('example-university', 'beginning-new-example');
 * const key = kdf.deriveChildKey('aes', 0);
 * console.log(kdf.fingerprint);
 * kdf.expire();
 */
async function eskdf(username, password) {
    // We are using closure + object instead of class because
    // we want to make `seed` non-accessible for any external function.
    let seed = deriveMainSeed(username, password);
    function deriveCK(protocol, accountId = 0, options) {
        (0, _assert_js_1.bytes)(seed, 32);
        const { salt, info } = getSaltInfo(protocol, accountId); // validate protocol & accountId
        const keyLength = getKeyLength(options); // validate options
        const key = (0, hkdf_js_1.hkdf)(sha256_js_1.sha256, seed, salt, info, keyLength);
        // Modulus has already been validated
        return options && 'modulus' in options ? modReduceKey(key, options.modulus) : key;
    }
    function expire() {
        if (seed)
            seed.fill(1);
        seed = undefined;
    }
    // prettier-ignore
    const fingerprint = Array.from(deriveCK('fingerprint', 0))
        .slice(0, 6)
        .map((char) => char.toString(16).padStart(2, '0').toUpperCase())
        .join(':');
    return Object.freeze({ deriveChildKey: deriveCK, expire, fingerprint });
}
exports.eskdf = eskdf;
//# sourceMappingURL=eskdf.js.map