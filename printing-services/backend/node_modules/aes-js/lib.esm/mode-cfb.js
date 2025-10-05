// Cipher Feedback
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
var _CFB_instances, _CFB_iv, _CFB_shiftRegister, _CFB_shift;
import { ModeOfOperation } from "./mode.js";
export class CFB extends ModeOfOperation {
    constructor(key, iv, segmentSize = 8) {
        super("CFB", key, CFB);
        _CFB_instances.add(this);
        _CFB_iv.set(this, void 0);
        _CFB_shiftRegister.set(this, void 0);
        // This library currently only handles byte-aligned segmentSize
        if (!Number.isInteger(segmentSize) || (segmentSize % 8)) {
            throw new TypeError("invalid segmentSize");
        }
        Object.defineProperties(this, {
            segmentSize: { enumerable: true, value: segmentSize }
        });
        if (iv) {
            if (iv.length % 16) {
                throw new TypeError("invalid iv size (must be 16 bytes)");
            }
            __classPrivateFieldSet(this, _CFB_iv, new Uint8Array(iv), "f");
        }
        else {
            __classPrivateFieldSet(this, _CFB_iv, new Uint8Array(16), "f");
        }
        __classPrivateFieldSet(this, _CFB_shiftRegister, this.iv, "f");
    }
    get iv() { return new Uint8Array(__classPrivateFieldGet(this, _CFB_iv, "f")); }
    encrypt(plaintext) {
        if (8 * plaintext.length % this.segmentSize) {
            throw new TypeError("invalid plaintext size (must be multiple of segmentSize bytes)");
        }
        const segmentSize = this.segmentSize / 8;
        const ciphertext = new Uint8Array(plaintext);
        for (let i = 0; i < ciphertext.length; i += segmentSize) {
            const xorSegment = this.aes.encrypt(__classPrivateFieldGet(this, _CFB_shiftRegister, "f"));
            for (let j = 0; j < segmentSize; j++) {
                ciphertext[i + j] ^= xorSegment[j];
            }
            __classPrivateFieldGet(this, _CFB_instances, "m", _CFB_shift).call(this, ciphertext.subarray(i));
        }
        return ciphertext;
    }
    decrypt(ciphertext) {
        if (8 * ciphertext.length % this.segmentSize) {
            throw new TypeError("invalid ciphertext size (must be multiple of segmentSize bytes)");
        }
        const segmentSize = this.segmentSize / 8;
        const plaintext = new Uint8Array(ciphertext);
        for (let i = 0; i < plaintext.length; i += segmentSize) {
            const xorSegment = this.aes.encrypt(__classPrivateFieldGet(this, _CFB_shiftRegister, "f"));
            for (let j = 0; j < segmentSize; j++) {
                plaintext[i + j] ^= xorSegment[j];
            }
            __classPrivateFieldGet(this, _CFB_instances, "m", _CFB_shift).call(this, ciphertext.subarray(i));
        }
        return plaintext;
    }
}
_CFB_iv = new WeakMap(), _CFB_shiftRegister = new WeakMap(), _CFB_instances = new WeakSet(), _CFB_shift = function _CFB_shift(data) {
    const segmentSize = this.segmentSize / 8;
    // Shift the register
    __classPrivateFieldGet(this, _CFB_shiftRegister, "f").set(__classPrivateFieldGet(this, _CFB_shiftRegister, "f").subarray(segmentSize));
    __classPrivateFieldGet(this, _CFB_shiftRegister, "f").set(data.subarray(0, segmentSize), 16 - segmentSize);
};
//# sourceMappingURL=mode-cfb.js.map