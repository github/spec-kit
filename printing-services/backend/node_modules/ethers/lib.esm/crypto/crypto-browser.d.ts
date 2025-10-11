declare global {
    interface Window {
    }
    const window: Window;
    const self: Window;
}
export interface CryptoHasher {
    update(data: Uint8Array): CryptoHasher;
    digest(): Uint8Array;
}
export declare function createHash(algo: string): CryptoHasher;
export declare function createHmac(_algo: string, key: Uint8Array): CryptoHasher;
export declare function pbkdf2Sync(password: Uint8Array, salt: Uint8Array, iterations: number, keylen: number, _algo: "sha256" | "sha512"): Uint8Array;
export declare function randomBytes(length: number): Uint8Array;
//# sourceMappingURL=crypto-browser.d.ts.map