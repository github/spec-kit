"use strict";
// Cipher Block Chaining
var __classPrivateFieldSet = (this && this.__classPrivateFieldSet) || function (receiver, state, value, kind, f) {
    if (kind === "m") throw new TypeError("Private method is not writable");
    if (kind === "a" && !f) throw new TypeError("Private accessor was defined without a setter");
    if (typeof state === "function" ? receiver !== state || !f : !state.has(receiver)) throw new TypeError("Cannot write private member to an object whose class did not declare it");
    return (kind === "a" ? f.call(receiver, value) : f ? f.value = value : state.set(receiver, value)), value;
};
var __classPrivateFieldGet = (this && this.__classPrivateFieldGet) || function (receiver, state, kind, f) {
    if (kind === "a" && !f) throw new TypeError("Private accessor was defined without a getter");
    if (typeof state === "function" ? receiver !== state || !f : !state.has(receiver)) throw new TypeError("Cannot read private member from an object whose class did not declare it");
    return kind === "m" ? f : kind === "a" ? f.call(receiver) : f ? f.value : state.get(receiver);
};
var _CBC_iv, _CBC_lastBlock;
Object.defineProperty(exports, "__esModule", { value: true });
exports.CBC = void 0;
const mode_js_1 = require("./mode.js");
class CBC extends mode_js_1.ModeOfOperation {
    constructor(key, iv) {
        super("ECC", key, CBC);
        _CBC_iv.set(this, void 0);
        _CBC_lastBlock.set(this, void 0);
        if (iv) {
            if (iv.length % 16) {
                throw new TypeError("invalid iv size (must be 16 bytes)");
            }
            __classPrivateFieldSet(this, _CBC_iv, new Uint8Array(iv), "f");
        }
        else {
            __classPrivateFieldSet(this, _CBC_iv, new Uint8Array(16), "f");
        }
        __classPrivateFieldSet(this, _CBC_lastBlock, this.iv, "f");
    }
    get iv() { return new Uint8Array(__classPrivateFieldGet(this, _CBC_iv, "f")); }
    encrypt(plaintext) {
        if (plaintext.length % 16) {
            throw new TypeError("invalid plaintext size (must be multiple of 16 bytes)");
        }
        const ciphertext = new Uint8Array(plaintext.length);
        for (let i = 0; i < plaintext.length; i += 16) {
            for (let j = 0; j < 16; j++) {
                __classPrivateFieldGet(this, _CBC_lastBlock, "f")[j] ^= plaintext[i + j];
            }
            __classPrivateFieldSet(this, _CBC_lastBlock, this.aes.encrypt(__classPrivateFieldGet(this, _CBC_lastBlock, "f")), "f");
            ciphertext.set(__classPrivateFieldGet(this, _CBC_lastBlock, "f"), i);
        }
        return ciphertext;
    }
    decrypt(ciphertext) {
        if (ciphertext.length % 16) {
            throw new TypeError("invalid ciphertext size (must be multiple of 16 bytes)");
        }
        const plaintext = new Uint8Array(ciphertext.length);
        for (let i = 0; i < ciphertext.length; i += 16) {
            const block = this.aes.decrypt(ciphertext.subarray(i, i + 16));
            for (let j = 0; j < 16; j++) {
                plaintext[i + j] = block[j] ^ __classPrivateFieldGet(this, _CBC_lastBlock, "f")[j];
                __classPrivateFieldGet(this, _CBC_lastBlock, "f")[j] = ciphertext[i + j];
            }
        }
        return plaintext;
    }
}
exports.CBC = CBC;
_CBC_iv = new WeakMap(), _CBC_lastBlock = new WeakMap();
//# sourceMappingURL=mode-cbc.js.map