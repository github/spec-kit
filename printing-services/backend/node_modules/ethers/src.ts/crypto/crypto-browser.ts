/* Browser Crypto Shims */

import { hmac } from "@noble/hashes/hmac";
import { pbkdf2 } from "@noble/hashes/pbkdf2";
import { sha256 } from "@noble/hashes/sha256";
import { sha512 } from "@noble/hashes/sha512";

import { assert, assertArgument } from "../utils/index.js";


declare global {
    interface Window { }

    const window: Window;
    const self: Window;
}


function getGlobal(): any {
  if (typeof self !== 'undefined') { return self; }
  if (typeof window !== 'undefined') { return window; }
  if (typeof global !== 'undefined') { return global; }
  throw new Error('unable to locate global object');
};

const anyGlobal = getGlobal();
const crypto: any = anyGlobal.crypto || anyGlobal.msCrypto;


export interface CryptoHasher {
    update(data: Uint8Array): CryptoHasher;
    digest(): Uint8Array;
}

export function createHash(algo: string): CryptoHasher {
    switch (algo) {
        case "sha256": return sha256.create();
        case "sha512": return sha512.create();
    }
    assertArgument(false, "invalid hashing algorithm name", "algorithm", algo);
}

export function createHmac(_algo: string, key: Uint8Array): CryptoHasher {
    const algo = ({ sha256, sha512 }[_algo]);
    assertArgument(algo != null, "invalid hmac algorithm", "algorithm", _algo);
    return hmac.create(algo, key);
}

export function pbkdf2Sync(password: Uint8Array, salt: Uint8Array, iterations: number, keylen: number, _algo: "sha256" | "sha512"): Uint8Array {
    const algo = ({ sha256, sha512 }[_algo]);
    assertArgument(algo != null, "invalid pbkdf2 algorithm", "algorithm", _algo);
    return pbkdf2(algo, password, salt, { c: iterations, dkLen: keylen });
}

export function randomBytes(length: number): Uint8Array {
    assert(crypto != null, "platform does not support secure random numbers", "UNSUPPORTED_OPERATION", {
        operation: "randomBytes" });

    assertArgument(Number.isInteger(length) && length > 0 && length <= 1024, "invalid length", "length", length);

    const result = new Uint8Array(length);
    crypto.getRandomValues(result);
    return result;
}
