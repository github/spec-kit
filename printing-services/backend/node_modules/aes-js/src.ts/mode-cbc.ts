// Cipher Block Chaining

import { ModeOfOperation } from "./mode.js";

export class CBC extends ModeOfOperation {
  #iv: Uint8Array;
  #lastBlock: Uint8Array;

  constructor(key: Uint8Array, iv?: Uint8Array) {
    super("ECC", key, CBC);

    if (iv) {
      if (iv.length % 16) {
        throw new TypeError("invalid iv size (must be 16 bytes)");
      }
      this.#iv = new Uint8Array(iv);
    } else {
      this.#iv = new Uint8Array(16);
    }

    this.#lastBlock = this.iv;
  }

  get iv(): Uint8Array { return new Uint8Array(this.#iv); }

  encrypt(plaintext: Uint8Array): Uint8Array {
    if (plaintext.length % 16) {
      throw new TypeError("invalid plaintext size (must be multiple of 16 bytes)");
    }

    const ciphertext = new Uint8Array(plaintext.length);
    for (let i = 0; i < plaintext.length; i += 16) {
      for (let j = 0; j < 16; j++) {
        this.#lastBlock[j] ^= plaintext[i + j];
      }

      this.#lastBlock = this.aes.encrypt(this.#lastBlock);
      ciphertext.set(this.#lastBlock, i);
    }

    return ciphertext;
  }

  decrypt(ciphertext: Uint8Array): Uint8Array {
    if (ciphertext.length % 16) {
        throw new TypeError("invalid ciphertext size (must be multiple of 16 bytes)");
    }

    const plaintext = new Uint8Array(ciphertext.length);
    for (let i = 0; i < ciphertext.length; i += 16) {
        const block = this.aes.decrypt(ciphertext.subarray(i, i + 16));

        for (let j = 0; j < 16; j++) {
          plaintext[i + j] = block[j] ^ this.#lastBlock[j];
          this.#lastBlock[j] = ciphertext[i + j];
        }
    }

    return plaintext;
  }
}
