import { ModeOfOperation } from "./mode.js";
export declare class CFB extends ModeOfOperation {
    #private;
    readonly segmentSize: number;
    constructor(key: Uint8Array, iv?: Uint8Array, segmentSize?: number);
    get iv(): Uint8Array;
    encrypt(plaintext: Uint8Array): Uint8Array;
    decrypt(ciphertext: Uint8Array): Uint8Array;
}
//# sourceMappingURL=mode-cfb.d.ts.map