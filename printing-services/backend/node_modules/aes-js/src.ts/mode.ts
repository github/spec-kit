
import { AES } from "./aes.js";

export abstract class ModeOfOperation {
  readonly aes!: AES;
  readonly name!: string;

  constructor(name: string, key: Uint8Array, cls?: any) {
    if (cls && !(this instanceof cls)) {
      throw new Error(`${ name } must be instantiated with "new"`);
    }

    Object.defineProperties(this, {
      aes: { enumerable: true, value: new AES(key) },
      name: { enumerable: true, value: name }
    });
  }

  abstract encrypt(plaintext: Uint8Array): Uint8Array;
  abstract decrypt(ciphertext: Uint8Array): Uint8Array;
}
