// Counter Mode

import { ModeOfOperation } from "./mode.js";

export class CTR extends ModeOfOperation {

  // Remaining bytes for the one-time pad
  #remaining: Uint8Array;
  #remainingIndex: number;

  // The current counter
  #counter: Uint8Array;

  constructor(key: Uint8Array, initialValue?: number | Uint8Array) {
    super("CTR", key, CTR);

    this.#counter = new Uint8Array(16)
    this.#counter.fill(0);

    this.#remaining = this.#counter;  // This will be discarded immediately
    this.#remainingIndex = 16;

    if (initialValue == null) { initialValue = 1; }

    if (typeof(initialValue) === "number") {
      this.setCounterValue(initialValue);
    } else {
      this.setCounterBytes(initialValue);
    }
  }

  get counter(): Uint8Array { return new Uint8Array(this.#counter); }

  setCounterValue(value: number): void {
    if (!Number.isInteger(value) || value < 0 || value > Number.MAX_SAFE_INTEGER) {
      throw new TypeError("invalid counter initial integer value");
    }

    for (let index = 15; index >= 0; --index) {
      this.#counter[index] = value % 256;
      value = Math.floor(value / 256);
    }
  }

  setCounterBytes(value: Uint8Array): void {
    if (value.length !== 16) {
      throw new TypeError("invalid counter initial Uint8Array value length");
    }

    this.#counter.set(value);
  }

  increment() {
    for (let i = 15; i >= 0; i--) {
      if (this.#counter[i] === 255) {
        this.#counter[i] = 0;
      } else {
        this.#counter[i]++;
        break;
      }
    }
  }

  encrypt(plaintext: Uint8Array): Uint8Array {
    const crypttext = new Uint8Array(plaintext);

    for (let i = 0; i < crypttext.length; i++) {
      if (this.#remainingIndex === 16) {
        this.#remaining = this.aes.encrypt(this.#counter);
        this.#remainingIndex = 0;
        this.increment();
      }
      crypttext[i] ^= this.#remaining[this.#remainingIndex++];
    }

    return crypttext;
  }

  decrypt(ciphertext: Uint8Array): Uint8Array {
    return this.encrypt(ciphertext);
  }
}
