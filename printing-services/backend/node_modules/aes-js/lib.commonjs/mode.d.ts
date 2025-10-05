import { AES } from "./aes.js";
export declare abstract class ModeOfOperation {
    readonly aes: AES;
    readonly name: string;
    constructor(name: string, key: Uint8Array, cls?: any);
    abstract encrypt(plaintext: Uint8Array): Uint8Array;
    abstract decrypt(ciphertext: Uint8Array): Uint8Array;
}
//# sourceMappingURL=mode.d.ts.map