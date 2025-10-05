/**
 *  A **Password-Based Key-Derivation Function** is designed to create
 *  a sequence of bytes suitible as a **key** from a human-rememberable
 *  password.
 *
 *  @_subsection: api/crypto:Passwords  [about-pbkdf]
 */
import type { BytesLike } from "../utils/index.js";
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
export declare function pbkdf2(_password: BytesLike, _salt: BytesLike, iterations: number, keylen: number, algo: "sha256" | "sha512"): string;
export declare namespace pbkdf2 {
    var _: (password: Uint8Array, salt: Uint8Array, iterations: number, keylen: number, algo: "sha256" | "sha512") => BytesLike;
    var lock: () => void;
    var register: (func: (password: Uint8Array, salt: Uint8Array, iterations: number, keylen: number, algo: "sha256" | "sha512") => BytesLike) => void;
}
//# sourceMappingURL=pbkdf2.d.ts.map