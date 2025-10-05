"use strict";
// Counter Mode
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
var _CTR_remaining, _CTR_remainingIndex, _CTR_counter;
Object.defineProperty(exports, "__esModule", { value: true });
exports.CTR = void 0;
const mode_js_1 = require("./mode.js");
class CTR extends mode_js_1.ModeOfOperation {
    constructor(key, initialValue) {
        super("CTR", key, CTR);
        // Remaining bytes for the one-time pad
        _CTR_remaining.set(this, void 0);
        _CTR_remainingIndex.set(this, void 0);
        // The current counter
        _CTR_counter.set(this, void 0);
        __classPrivateFieldSet(this, _CTR_counter, new Uint8Array(16), "f");
        __classPrivateFieldGet(this, _CTR_counter, "f").fill(0);
        __classPrivateFieldSet(this, _CTR_remaining, __classPrivateFieldGet(this, _CTR_counter, "f"), "f"); // This will be discarded immediately
        __classPrivateFieldSet(this, _CTR_remainingIndex, 16, "f");
        if (initialValue == null) {
            initialValue = 1;
        }
        if (typeof (initialValue) === "number") {
            this.setCounterValue(initialValue);
        }
        else {
            this.setCounterBytes(initialValue);
        }
    }
    get counter() { return new Uint8Array(__classPrivateFieldGet(this, _CTR_counter, "f")); }
    setCounterValue(value) {
        if (!Number.isInteger(value) || value < 0 || value > Number.MAX_SAFE_INTEGER) {
            throw new TypeError("invalid counter initial integer value");
        }
        for (let index = 15; index >= 0; --index) {
            __classPrivateFieldGet(this, _CTR_counter, "f")[index] = value % 256;
            value = Math.floor(value / 256);
        }
    }
    setCounterBytes(value) {
        if (value.length !== 16) {
            throw new TypeError("invalid counter initial Uint8Array value length");
        }
        __classPrivateFieldGet(this, _CTR_counter, "f").set(value);
    }
    increment() {
        for (let i = 15; i >= 0; i--) {
            if (__classPrivateFieldGet(this, _CTR_counter, "f")[i] === 255) {
                __classPrivateFieldGet(this, _CTR_counter, "f")[i] = 0;
            }
            else {
                __classPrivateFieldGet(this, _CTR_counter, "f")[i]++;
                break;
            }
        }
    }
    encrypt(plaintext) {
        var _a, _b;
        const crypttext = new Uint8Array(plaintext);
        for (let i = 0; i < crypttext.length; i++) {
            if (__classPrivateFieldGet(this, _CTR_remainingIndex, "f") === 16) {
                __classPrivateFieldSet(this, _CTR_remaining, this.aes.encrypt(__classPrivateFieldGet(this, _CTR_counter, "f")), "f");
                __classPrivateFieldSet(this, _CTR_remainingIndex, 0, "f");
                this.increment();
            }
            crypttext[i] ^= __classPrivateFieldGet(this, _CTR_remaining, "f")[__classPrivateFieldSet(this, _CTR_remainingIndex, (_b = __classPrivateFieldGet(this, _CTR_remainingIndex, "f"), _a = _b++, _b), "f"), _a];
        }
        return crypttext;
    }
    decrypt(ciphertext) {
        return this.encrypt(ciphertext);
    }
}
exports.CTR = CTR;
_CTR_remaining = new WeakMap(), _CTR_remainingIndex = new WeakMap(), _CTR_counter = new WeakMap();
//# sourceMappingURL=mode-ctr.js.map