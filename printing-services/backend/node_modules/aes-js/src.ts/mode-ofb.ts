// Output Feedback

import { ModeOfOperation } from "./mode.js";

export class OFB extends ModeOfOperation {
  #iv: Uint8Array;
  #lastPrecipher: Uint8Array;
  #lastPrecipherIndex: number;

  constructor(key: Uint8Array, iv?: Uint8Array) {
    super("OFB", key, OFB);

    if (iv) {
      if (iv.length % 16) {
        throw new TypeError("invalid iv size (must be 16 bytes)");
      }
      this.#iv = new Uint8Array(iv);
    } else {
      this.#iv = new Uint8Array(16);
    }

    this.#lastPrecipher = this.iv;
    this.#lastPrecipherIndex = 16;
  }

  get iv(): Uint8Array { return new Uint8Array(this.#iv); }

  encrypt(plaintext: Uint8Array): Uint8Array {
    if (plaintext.length % 16) {
      throw new TypeError("invalid plaintext size (must be multiple of 16 bytes)");
    }

    const ciphertext = new Uint8Array(plaintext);
    for (let i = 0; i < ciphertext.length; i++) {
      if (this.#lastPrecipherIndex === 16) {
          this.#lastPrecipher = this.aes.encrypt(this.#lastPrecipher);
          this.#lastPrecipherIndex = 0;
      }
      ciphertext[i] ^= this.#lastPrecipher[this.#lastPrecipherIndex++];
    }

    return ciphertext;
  }

  decrypt(ciphertext: Uint8Array): Uint8Array {
    if (ciphertext.length % 16) {
        throw new TypeError("invalid ciphertext size (must be multiple of 16 bytes)");
    }
    return this.encrypt(ciphertext);
  }
}
