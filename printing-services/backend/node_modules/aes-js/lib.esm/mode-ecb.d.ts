import { ModeOfOperation } from "./mode.js";
export declare class ECB extends ModeOfOperation {
    constructor(key: Uint8Array);
    encrypt(plaintext: Uint8Array): Uint8Array;
    decrypt(crypttext: Uint8Array): Uint8Array;
}
//# sourceMappingURL=mode-ecb.d.ts.map