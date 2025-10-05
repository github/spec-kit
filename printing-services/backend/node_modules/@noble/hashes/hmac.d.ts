import { Hash, CHash, Input } from './utils.js';
export declare class HMAC<T extends Hash<T>> extends Hash<HMAC<T>> {
    oHash: T;
    iHash: T;
    blockLen: number;
    outputLen: number;
    private finished;
    private destroyed;
    constructor(hash: CHash, _key: Input);
    update(buf: Input): this;
    digestInto(out: Uint8Array): void;
    digest(): Uint8Array;
    _cloneInto(to?: HMAC<T>): HMAC<T>;
    destroy(): void;
}
/**
 * HMAC: RFC2104 message authentication code.
 * @param hash - function that would be used e.g. sha256
 * @param key - message key
 * @param message - message data
 */
export declare const hmac: {
    (hash: CHash, key: Input, message: Input): Uint8Array;
    create(hash: CHash, key: Input): HMAC<any>;
};
