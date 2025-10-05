// Cipher Feedback

import { ModeOfOperation } from "./mode.js";

export class CFB extends ModeOfOperation {
  #iv: Uint8Array;
  #shiftRegister: Uint8Array;

  readonly segmentSize!: number;

  constructor(key: Uint8Array, iv?: Uint8Array, segmentSize: number = 8) {
    super("CFB", key, CFB);

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
      this.#iv = new Uint8Array(iv);
    } else {
      this.#iv = new Uint8Array(16);
    }

    this.#shiftRegister = this.iv;
  }

  get iv(): Uint8Array { return new Uint8Array(this.#iv); }

  #shift(data: Uint8Array): void {
    const segmentSize = this.segmentSize / 8;

    // Shift the register
    this.#shiftRegister.set(this.#shiftRegister.subarray(segmentSize));
    this.#shiftRegister.set(data.subarray(0, segmentSize), 16 - segmentSize);
  }

  encrypt(plaintext: Uint8Array): Uint8Array {
    if (8 * plaintext.length % this.segmentSize) {
      throw new TypeError("invalid plaintext size (must be multiple of segmentSize bytes)");
    }

    const segmentSize = this.segmentSize / 8;

    const ciphertext = new Uint8Array(plaintext);

    for (let i = 0; i < ciphertext.length; i += segmentSize) {
      const xorSegment = this.aes.encrypt(this.#shiftRegister);
      for (let j = 0; j < segmentSize; j++) {
        ciphertext[i + j] ^= xorSegment[j];
      }

      this.#shift(ciphertext.subarray(i));
    }

    return ciphertext;
  }

  decrypt(ciphertext: Uint8Array): Uint8Array {
    if (8 * ciphertext.length % this.segmentSize) {
        throw new TypeError("invalid ciphertext size (must be multiple of segmentSize bytes)");
    }

    const segmentSize = this.segmentSize / 8;

    const plaintext = new Uint8Array(ciphertext);

    for (let i = 0; i < plaintext.length; i += segmentSize) {
      const xorSegment = this.aes.encrypt(this.#shiftRegister);
      for (let j = 0; j < segmentSize; j++) {
        plaintext[i + j] ^= xorSegment[j];
      }

      this.#shift(ciphertext.subarray(i));
    }

    return plaintext;
  }
}
