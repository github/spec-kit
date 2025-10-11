import { ModeOfOperation } from "./mode.js";
export declare class CBC extends ModeOfOperation {
    #private;
    constructor(key: Uint8Array, iv?: Uint8Array);
    get iv(): Uint8Array;
    encrypt(plaintext: Uint8Array): Uint8Array;
    decrypt(ciphertext: Uint8Array): Uint8Array;
}
//# sourceMappingURL=mode-cbc.d.ts.map