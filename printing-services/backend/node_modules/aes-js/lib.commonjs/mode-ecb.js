"use strict";
// Electronic Code Book
Object.defineProperty(exports, "__esModule", { value: true });
exports.ECB = void 0;
const mode_js_1 = require("./mode.js");
class ECB extends mode_js_1.ModeOfOperation {
    constructor(key) {
        super("ECB", key, ECB);
    }
    encrypt(plaintext) {
        if (plaintext.length % 16) {
            throw new TypeError("invalid plaintext size (must be multiple of 16 bytes)");
        }
        const crypttext = new Uint8Array(plaintext.length);
        for (let i = 0; i < plaintext.length; i += 16) {
            crypttext.set(this.aes.encrypt(plaintext.subarray(i, i + 16)), i);
        }
        return crypttext;
    }
    decrypt(crypttext) {
        if (crypttext.length % 16) {
            throw new TypeError("invalid ciphertext size (must be multiple of 16 bytes)");
        }
        const plaintext = new Uint8Array(crypttext.length);
        for (let i = 0; i < crypttext.length; i += 16) {
            plaintext.set(this.aes.decrypt(crypttext.subarray(i, i + 16)), i);
        }
        return plaintext;
    }
}
exports.ECB = ECB;
//# sourceMappingURL=mode-ecb.js.map