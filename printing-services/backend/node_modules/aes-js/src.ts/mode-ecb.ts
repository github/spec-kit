// Electronic Code Book

import { ModeOfOperation } from "./mode.js";

export class ECB extends ModeOfOperation {

  constructor(key: Uint8Array) {
    super("ECB", key, ECB);
  }

  encrypt(plaintext: Uint8Array): Uint8Array {
    if (plaintext.length % 16) {
        throw new TypeError("invalid plaintext size (must be multiple of 16 bytes)");
    }

    const crypttext = new Uint8Array(plaintext.length);
    for (let i = 0; i < plaintext.length; i += 16) {
        crypttext.set(this.aes.encrypt(plaintext.subarray(i, i + 16)), i);
    }

    return crypttext;
  }

  decrypt(crypttext: Uint8Array): Uint8Array {
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
