/**
 *  A **Password-Based Key-Derivation Function** is designed to create
 *  a sequence of bytes suitible as a **key** from a human-rememberable
 *  password.
 *
 *  @_subsection: api/crypto:Passwords  [about-pbkdf]
 */

import { pbkdf2Sync } from "./crypto.js";

import { getBytes, hexlify } from "../utils/index.js";

import type { BytesLike } from "../utils/index.js";


let locked = false;

const _pbkdf2 = function(password: Uint8Array, salt: Uint8Array, iterations: number, keylen: number, algo: "sha256" | "sha512"): BytesLike {
    return pbkdf2Sync(password, salt, iterations, keylen, algo);
}

let __pbkdf2 = _pbkdf2;

/**
 *  Return the [[link-pbkdf2]] for %%keylen%% bytes for %%password%% using
 *  the %%salt%% and using %%iterations%% of %%algo%%.
 *
 *  This PBKDF is outdated and should not be used in new projects, but is
 *  required to decrypt older files.
 *
 *  @example:
 *    // The password must be converted to bytes, and it is generally
 *    // best practices to ensure the string has been normalized. Many
 *    // formats explicitly indicate the normalization form to use.
 *    password = "hello"
 *    passwordBytes = toUtf8Bytes(password, "NFKC")
 *
 *    salt = id("some-salt")
 *
 *    // Compute the PBKDF2
 *    pbkdf2(passwordBytes, salt, 1024, 16, "sha256")
 *    //_result:
 */
export function pbkdf2(_password: BytesLike, _salt: BytesLike, iterations: number, keylen: number, algo: "sha256" | "sha512"): string {
    const password = getBytes(_password, "password");
    const salt = getBytes(_salt, "salt");
    return hexlify(__pbkdf2(password, salt, iterations, keylen, algo));
}
pbkdf2._ = _pbkdf2;
pbkdf2.lock = function(): void { locked = true; }
pbkdf2.register = function(func: (password: Uint8Array, salt: Uint8Array, iterations: number, keylen: number, algo: "sha256" | "sha512") => BytesLike) {
    if (locked) { throw new Error("pbkdf2 is locked"); }
    __pbkdf2 = func;
}
Object.freeze(pbkdf2);
