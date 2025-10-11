import { ModeOfOperation } from "./mode.js";
export declare class CTR extends ModeOfOperation {
    #private;
    constructor(key: Uint8Array, initialValue?: number | Uint8Array);
    get counter(): Uint8Array;
    setCounterValue(value: number): void;
    setCounterBytes(value: Uint8Array): void;
    increment(): void;
    encrypt(plaintext: Uint8Array): Uint8Array;
    decrypt(ciphertext: Uint8Array): Uint8Array;
}
//# sourceMappingURL=mode-ctr.d.ts.map