/*! MIT License. Copyright 2015-2022 Richard Moore <me@ricmoo.com>. See LICENSE.txt. */
export declare class AES {
    #private;
    get key(): Uint8Array;
    constructor(key: Uint8Array);
    encrypt(plaintext: Uint8Array): Uint8Array;
    decrypt(ciphertext: Uint8Array): Uint8Array;
}
//# sourceMappingURL=aes.d.ts.map