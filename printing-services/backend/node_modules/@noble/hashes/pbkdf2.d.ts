import { CHash, Input } from './utils.js';
export type Pbkdf2Opt = {
    c: number;
    dkLen?: number;
    asyncTick?: number;
};
/**
 * PBKDF2-HMAC: RFC 2898 key derivation function
 * @param hash - hash function that would be used e.g. sha256
 * @param password - password from which a derived key is generated
 * @param salt - cryptographic salt
 * @param opts - {c, dkLen} where c is work factor and dkLen is output message size
 */
export declare function pbkdf2(hash: CHash, password: Input, salt: Input, opts: Pbkdf2Opt): Uint8Array;
export declare function pbkdf2Async(hash: CHash, password: Input, salt: Input, opts: Pbkdf2Opt): Promise<Uint8Array>;
